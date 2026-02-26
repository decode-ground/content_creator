# AWS Setup Guide — Script-to-Movie

A step-by-step guide to deploying this app on AWS. Written for someone with no prior AWS experience. Each section tells you what to do and gives you the commands to run (or to ask Claude Code to run for you).

## What You're Setting Up

| AWS Service | What it does for this app |
|-------------|--------------------------|
| **EC2** | Runs the backend (FastAPI) and frontend (React + Express) servers |
| **S3** | Stores uploaded images, generated videos, and final movies |
| **RDS (MySQL)** | Hosts the database (the app uses SQL — see note on DynamoDB below) |

### Why RDS Instead of DynamoDB?

This app uses MySQL with SQLAlchemy ORM — relational tables with foreign keys, joins, and ordered queries (e.g., scenes linked to projects, videos linked to scenes). DynamoDB is a NoSQL key-value store that doesn't support any of those patterns. Switching to DynamoDB would mean rewriting every model and query in the app.

**RDS for MySQL** is the right choice here. It's the same MySQL you use locally during development, but hosted and managed by AWS. Zero code changes — you just swap the database URL in your `.env` file.

| | Local Development | Production (RDS) |
|---|---|---|
| Database | MySQL on your machine | MySQL on AWS RDS |
| Connection | `localhost:3306` | `your-instance.us-east-1.rds.amazonaws.com:3306` |
| Code changes | None | None — just change `DATABASE_URL` in `.env` |

---

## Prerequisites

Before you start, you need:

1. **An AWS account** — sign up at https://aws.amazon.com (requires a credit card; there's a free tier for the first 12 months)
2. **AWS CLI installed** on your machine
3. **Claude Code** — you'll use this to run commands and edit config files

### Install the AWS CLI

Ask Claude Code to run:

```bash
# macOS
brew install awscli

# Or download directly
# https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

# Verify it worked
aws --version
```

---

## Step 1: Create an IAM User

IAM (Identity and Access Management) controls who can do what in your AWS account. You need a user with programmatic access.

1. Go to https://console.aws.amazon.com/iam
2. Click **Users** in the left sidebar, then **Create user**
3. Username: `script-to-movie-admin`
4. Check **Provide user access to the AWS Management Console** (optional, for web dashboard access)
5. Click **Next**, then **Attach policies directly**
6. Search for and check these policies:
   - `AmazonS3FullAccess`
   - `AmazonRDSFullAccess`
   - `AmazonEC2FullAccess`
7. Click **Next**, then **Create user**
8. Click on the user, go to **Security credentials** tab
9. Click **Create access key** → select **Command Line Interface (CLI)**
10. Save the **Access Key ID** and **Secret Access Key** — you'll need them in the next step

### Configure the AWS CLI

Ask Claude Code to run:

```bash
aws configure
```

It will prompt you for:

```
AWS Access Key ID: (paste your access key)
AWS Secret Access Key: (paste your secret key)
Default region name: us-east-1
Default output format: json
```

Verify it works:

```bash
aws sts get-caller-identity
```

You should see your account ID and user ARN.

---

## Step 2: Create an S3 Bucket

S3 is where the app stores all media files (storyboard images, video clips, final movies).

```bash
# Pick a globally unique name (S3 bucket names are shared across all AWS accounts)
aws s3 mb s3://script-to-movie-media-YOURNAME --region us-east-1
```

Replace `YOURNAME` with something unique (e.g., your name or a random string).

### Configure CORS (so the frontend can load media)

Create a file called `cors.json`:

```json
{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST"],
      "AllowedOrigins": ["*"],
      "ExposeHeaders": ["ETag"],
      "MaxAgeSeconds": 3600
    }
  ]
}
```

Apply it:

```bash
aws s3api put-bucket-cors --bucket script-to-movie-media-YOURNAME --cors-configuration file://cors.json
```

### Set the bucket policy for public read access (for video playback)

Create a file called `bucket-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::script-to-movie-media-YOURNAME/*"
    }
  ]
}
```

Apply it:

```bash
# First disable the "block public access" setting
aws s3api put-public-access-block --bucket script-to-movie-media-YOURNAME \
  --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

# Then apply the policy
aws s3api put-bucket-policy --bucket script-to-movie-media-YOURNAME --policy file://bucket-policy.json
```

Write down your bucket name — you'll need it for the `.env` file later.

---

## Step 3: Create an RDS MySQL Database

### What is RDS?

RDS (Relational Database Service) is AWS's managed database hosting. Think of it as MySQL running on a server that AWS maintains for you. You get:

- **Automatic backups** — AWS backs up your database daily, you can restore to any point in the last 7 days
- **Automatic patching** — security updates applied without you doing anything
- **Monitoring** — CPU, memory, storage, and connection metrics in the AWS console
- **Scaling** — upgrade to a bigger instance with a few clicks if you need more power

You access it the same way you access your local MySQL — with a hostname, port, username, and password. The only difference is the hostname points to AWS instead of `localhost`.

### Free Tier

If your AWS account is less than 12 months old, RDS is free within these limits:

- **750 hours/month** of `db.t3.micro` (enough to run 24/7, since a month is ~730 hours)
- **20 GB** of database storage
- **20 GB** of backup storage

After the free tier expires, `db.t3.micro` costs about $15/month.

### 3a. Create a security group for the database

A security group is a firewall that controls who can connect to your database.

```bash
aws ec2 create-security-group \
  --group-name script-to-movie-db-sg \
  --description "Security group for Script-to-Movie RDS" \
  --region us-east-1
```

Save the `GroupId` from the output (looks like `sg-0abc1234def56789`).

```bash
# Allow MySQL traffic (port 3306)
# For now we open it to all IPs so you can connect from your local machine and EC2.
# For tighter security later, restrict this to only your EC2 security group.
aws ec2 authorize-security-group-ingress \
  --group-id sg-YOUR_GROUP_ID \
  --protocol tcp \
  --port 3306 \
  --cidr 0.0.0.0/0
```

### 3b. Create the RDS instance

```bash
aws rds create-db-instance \
  --db-instance-identifier script-to-movie-db \
  --db-instance-class db.t3.micro \
  --engine mysql \
  --engine-version "8.0" \
  --master-username admin \
  --master-user-password CHOOSE_A_STRONG_PASSWORD \
  --allocated-storage 20 \
  --storage-type gp2 \
  --vpc-security-group-ids sg-YOUR_GROUP_ID \
  --publicly-accessible \
  --backup-retention-period 7 \
  --region us-east-1
```

What each flag means:

| Flag | What it does |
|------|-------------|
| `--db-instance-class db.t3.micro` | Smallest instance size (free tier eligible) |
| `--engine mysql --engine-version "8.0"` | MySQL 8, same version you use locally |
| `--master-username admin` | The database admin username |
| `--master-user-password` | Your database password — pick something strong |
| `--allocated-storage 20` | 20 GB disk space (free tier max) |
| `--publicly-accessible` | Allows connections from outside AWS (your local machine) |
| `--backup-retention-period 7` | Keep daily backups for 7 days |

### 3c. Wait for it to be ready

This takes 5-10 minutes. Check the status:

```bash
aws rds describe-db-instances \
  --db-instance-identifier script-to-movie-db \
  --query "DBInstances[0].DBInstanceStatus"
```

Keep running this until it says `"available"`.

### 3d. Get the connection endpoint

```bash
aws rds describe-db-instances \
  --db-instance-identifier script-to-movie-db \
  --query "DBInstances[0].Endpoint.Address" \
  --output text
```

This gives you something like:

```
script-to-movie-db.abc123xyz.us-east-1.rds.amazonaws.com
```

Save this — it's your database hostname.

### 3e. Create the database

Connect to your new RDS instance and create the `script_to_movie` database:

```bash
mysql -h script-to-movie-db.abc123xyz.us-east-1.rds.amazonaws.com -u admin -p -e "CREATE DATABASE script_to_movie;"
```

It will prompt you for the password you chose in step 3b.

### 3f. Update your `.env` to use RDS

This is the only change needed to switch from local MySQL to RDS:

```bash
# Before (local development)
DATABASE_URL=mysql+aiomysql://root:password@localhost:3306/script_to_movie

# After (production with RDS)
DATABASE_URL=mysql+aiomysql://admin:YOUR_PASSWORD@script-to-movie-db.abc123xyz.us-east-1.rds.amazonaws.com:3306/script_to_movie
```

Then run migrations to create the tables:

```bash
cd script_to_movie/backend
source .venv/bin/activate
alembic upgrade head
```

### Accessing RDS After Setup

Here are the commands you'll use day-to-day to manage your database:

```bash
# Check the instance status
aws rds describe-db-instances \
  --db-instance-identifier script-to-movie-db \
  --query "DBInstances[0].{Status:DBInstanceStatus,Endpoint:Endpoint.Address,Storage:AllocatedStorage}"

# Connect directly with mysql CLI (for debugging)
mysql -h YOUR_RDS_ENDPOINT -u admin -p script_to_movie

# Stop the instance (to save money when not in use)
aws rds stop-db-instance --db-instance-identifier script-to-movie-db

# Start it back up
aws rds start-db-instance --db-instance-identifier script-to-movie-db

# View it in the AWS web console
# Go to: https://console.aws.amazon.com/rds → Databases → script-to-movie-db
```

You can also manage everything from the **AWS Console** (the web dashboard) at https://console.aws.amazon.com/rds. It shows you metrics, lets you create snapshots, resize the instance, and more — all through a visual interface.

---

## Step 4: Launch an EC2 Instance

EC2 is a virtual server that will run your app.

### Create a key pair (for SSH access)

```bash
aws ec2 create-key-pair \
  --key-name script-to-movie-key \
  --query "KeyMaterial" \
  --output text > ~/.ssh/script-to-movie-key.pem

chmod 400 ~/.ssh/script-to-movie-key.pem
```

### Create a security group for EC2

```bash
aws ec2 create-security-group \
  --group-name script-to-movie-ec2-sg \
  --description "Security group for Script-to-Movie EC2"
```

Save the `GroupId`.

```bash
# Allow SSH (port 22), backend (port 8000), and frontend (port 5173/3000)
EC2_SG=sg-YOUR_EC2_GROUP_ID

aws ec2 authorize-security-group-ingress --group-id $EC2_SG --protocol tcp --port 22 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $EC2_SG --protocol tcp --port 8000 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $EC2_SG --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $EC2_SG --protocol tcp --port 443 --cidr 0.0.0.0/0
```

### Launch the instance

```bash
# Ubuntu 22.04 LTS (free-tier eligible)
# t3.medium recommended for video processing (ffmpeg needs some memory)
aws ec2 run-instances \
  --image-id ami-0c7217cdde317cfec \
  --instance-type t3.medium \
  --key-name script-to-movie-key \
  --security-group-ids sg-YOUR_EC2_GROUP_ID \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":30}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=script-to-movie}]' \
  --region us-east-1
```

Get the public IP:

```bash
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=script-to-movie" \
  --query "Reservations[0].Instances[0].PublicIpAddress" \
  --output text
```

### SSH into the instance

```bash
ssh -i ~/.ssh/script-to-movie-key.pem ubuntu@YOUR_PUBLIC_IP
```

---

## Step 5: Set Up the EC2 Server

Run these commands on the EC2 instance (after SSH-ing in):

```bash
# System packages
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3.11 python3.11-venv python3-pip \
  ffmpeg mysql-client git curl

# Install Node.js 20 (for the frontend)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install pnpm (the frontend package manager)
npm install -g pnpm
```

### Clone the repo

```bash
cd /home/ubuntu
git clone YOUR_REPO_URL script-to-movie
cd script-to-movie
```

### Set up the backend

```bash
cd script_to_movie/backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Create the backend `.env` file

```bash
cat > .env << 'EOF'
# Database — point to your RDS instance
DATABASE_URL=mysql+aiomysql://admin:YOUR_RDS_PASSWORD@YOUR_RDS_ENDPOINT:3306/script_to_movie

# JWT
JWT_SECRET=GENERATE_A_LONG_RANDOM_STRING_HERE

# Anthropic
ANTHROPIC_API_KEY=sk-ant-YOUR_KEY

# Kling AI
KLING_API_KEY=your-kling-key
KLING_SECRET_KEY=your-kling-secret

# AWS S3
AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
AWS_REGION=us-east-1
S3_BUCKET=script-to-movie-media-YOURNAME

# App
DEBUG=false
CORS_ORIGINS=["http://YOUR_PUBLIC_IP","http://YOUR_PUBLIC_IP:5173"]
EOF
```

Replace all placeholder values with your actual credentials.

### Set up the frontend

```bash
cd /home/ubuntu/script-to-movie/script_to_movie
pnpm install
pnpm build
```

---

## Step 6: Run the App with systemd

systemd keeps the app running in the background and restarts it if it crashes.

### Backend service

```bash
sudo tee /etc/systemd/system/stm-backend.service << 'EOF'
[Unit]
Description=Script-to-Movie Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/script-to-movie/script_to_movie/backend
ExecStart=/home/ubuntu/script-to-movie/script_to_movie/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
Environment=PATH=/home/ubuntu/script-to-movie/script_to_movie/backend/.venv/bin:/usr/bin

[Install]
WantedBy=multi-user.target
EOF
```

### Frontend service

```bash
sudo tee /etc/systemd/system/stm-frontend.service << 'EOF'
[Unit]
Description=Script-to-Movie Frontend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/script-to-movie/script_to_movie
ExecStart=/usr/bin/node dist/index.js
Restart=always
RestartSec=5
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
EOF
```

### Start both services

```bash
sudo systemctl daemon-reload
sudo systemctl enable stm-backend stm-frontend
sudo systemctl start stm-backend stm-frontend
```

### Check that they're running

```bash
sudo systemctl status stm-backend
sudo systemctl status stm-frontend

# View logs
sudo journalctl -u stm-backend -f
sudo journalctl -u stm-frontend -f
```

---

## Step 7: Verify Everything Works

From your local machine:

```bash
# Backend health check
curl http://YOUR_PUBLIC_IP:8000/docs

# Frontend
open http://YOUR_PUBLIC_IP:5173
```

---

## How to Use Claude Code for All of This

You can ask Claude Code to do each step for you. Examples:

- "Run `aws configure` and set up my credentials"
- "Create an S3 bucket called script-to-movie-media-xyz"
- "SSH into my EC2 instance at 1.2.3.4 and install the dependencies"
- "Create the systemd service files on my EC2 instance"
- "Read the backend logs on my EC2 and help me debug the error"

Claude Code can run all the `aws` CLI commands, edit `.env` files, and SSH into your server to set things up.

---

## Cost Estimate (Monthly)

| Service | Spec | Estimated Cost |
|---------|------|---------------|
| EC2 | t3.medium (2 vCPU, 4 GB RAM) | ~$30/mo |
| RDS MySQL | db.t3.micro (free first 12 months, ~$15/mo after) | Free → ~$15/mo |
| S3 | Storage + requests | ~$1-5/mo (depends on video count) |
| Data transfer | Outbound bandwidth | ~$1-10/mo |

**Total: roughly $30-60/month** after the free tier period.

To reduce costs:
- Use `t3.micro` for EC2 if you don't need heavy video processing on the server (ffmpeg runs there)
- Use Reserved Instances for EC2/RDS if you plan to run it long-term (up to 72% savings)
- Set up S3 lifecycle rules to delete old videos after 90 days

---

## Quick Reference: Environment Variables

These are the values you need to collect during setup and put in `backend/.env`:

| Variable | Where to find it |
|----------|-----------------|
| `DATABASE_URL` | Step 3 — RDS endpoint + your password |
| `AWS_ACCESS_KEY_ID` | Step 1 — IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | Step 1 — IAM user secret key |
| `AWS_REGION` | `us-east-1` (or whichever region you chose) |
| `S3_BUCKET` | Step 2 — the bucket name you created |
| `ANTHROPIC_API_KEY` | From https://console.anthropic.com |
| `KLING_API_KEY` | From Kling AI dashboard |
| `JWT_SECRET` | Generate one: `openssl rand -hex 32` |

---

## Troubleshooting

**"Connection refused" on port 8000**
- Check the backend is running: `sudo systemctl status stm-backend`
- Check the security group allows port 8000

**"Access Denied" on S3 uploads**
- Verify your IAM user has `AmazonS3FullAccess`
- Verify `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in `.env` are correct

**"Can't connect to MySQL server"**
- Check the RDS instance is in `available` state
- Check the RDS security group allows port 3306 from the EC2 security group
- Verify the `DATABASE_URL` endpoint is correct

**ffmpeg errors during video assembly**
- Make sure ffmpeg is installed on EC2: `ffmpeg -version`
- If not: `sudo apt-get install -y ffmpeg`
