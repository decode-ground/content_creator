import bcrypt from "bcrypt";
import { nanoid } from "nanoid";
import { eq } from "drizzle-orm";
import { getDb } from "../db";
import { users } from "../../drizzle/schema";

const SALT_ROUNDS = 10;

export type RegisterInput = {
  email: string;
  password: string;
  name: string;
};

export type LoginInput = {
  email: string;
  password: string;
};

export type AuthUser = {
  id: number;
  openId: string;
  email: string;
  name: string | null;
  role: "user" | "admin";
};

export class AuthError extends Error {
  constructor(
    message: string,
    public code: "INVALID_CREDENTIALS" | "EMAIL_EXISTS" | "USER_NOT_FOUND" | "INVALID_INPUT"
  ) {
    super(message);
    this.name = "AuthError";
  }
}

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, SALT_ROUNDS);
}

export async function verifyPassword(
  password: string,
  hash: string
): Promise<boolean> {
  return bcrypt.compare(password, hash);
}

export async function registerUser(input: RegisterInput): Promise<AuthUser> {
  const { email, password, name } = input;

  if (!email || !password || !name) {
    throw new AuthError("Email, password, and name are required", "INVALID_INPUT");
  }

  if (password.length < 8) {
    throw new AuthError("Password must be at least 8 characters", "INVALID_INPUT");
  }

  const db = await getDb();
  if (!db) {
    throw new Error("Database not available");
  }

  // Check if email already exists
  const existing = await db
    .select()
    .from(users)
    .where(eq(users.email, email.toLowerCase()))
    .limit(1);

  if (existing.length > 0) {
    throw new AuthError("An account with this email already exists", "EMAIL_EXISTS");
  }

  // Hash password and create user
  const passwordHash = await hashPassword(password);
  const openId = `user_${nanoid(16)}`;

  await db.insert(users).values({
    openId,
    email: email.toLowerCase(),
    name,
    passwordHash,
    loginMethod: "email",
    lastSignedIn: new Date(),
  });

  // Fetch the created user
  const [newUser] = await db
    .select()
    .from(users)
    .where(eq(users.openId, openId))
    .limit(1);

  return {
    id: newUser.id,
    openId: newUser.openId,
    email: newUser.email!,
    name: newUser.name,
    role: newUser.role,
  };
}

export async function loginUser(input: LoginInput): Promise<AuthUser> {
  const { email, password } = input;

  if (!email || !password) {
    throw new AuthError("Email and password are required", "INVALID_INPUT");
  }

  const db = await getDb();
  if (!db) {
    throw new Error("Database not available");
  }

  // Find user by email
  const [user] = await db
    .select()
    .from(users)
    .where(eq(users.email, email.toLowerCase()))
    .limit(1);

  if (!user) {
    throw new AuthError("Invalid email or password", "INVALID_CREDENTIALS");
  }

  if (!user.passwordHash) {
    throw new AuthError("Invalid email or password", "INVALID_CREDENTIALS");
  }

  // Verify password
  const isValid = await verifyPassword(password, user.passwordHash);
  if (!isValid) {
    throw new AuthError("Invalid email or password", "INVALID_CREDENTIALS");
  }

  // Update last signed in
  await db
    .update(users)
    .set({ lastSignedIn: new Date() })
    .where(eq(users.id, user.id));

  return {
    id: user.id,
    openId: user.openId,
    email: user.email!,
    name: user.name,
    role: user.role,
  };
}

export async function getUserByEmail(email: string): Promise<AuthUser | null> {
  const db = await getDb();
  if (!db) {
    return null;
  }

  const [user] = await db
    .select()
    .from(users)
    .where(eq(users.email, email.toLowerCase()))
    .limit(1);

  if (!user) {
    return null;
  }

  return {
    id: user.id,
    openId: user.openId,
    email: user.email!,
    name: user.name,
    role: user.role,
  };
}
