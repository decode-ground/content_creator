CREATE TABLE `characters` (
	`id` int AUTO_INCREMENT NOT NULL,
	`projectId` int NOT NULL,
	`name` varchar(255) NOT NULL,
	`description` text NOT NULL,
	`visualDescription` text,
	`imageUrl` varchar(512),
	`imageKey` varchar(512),
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `characters_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `finalMovies` (
	`id` int AUTO_INCREMENT NOT NULL,
	`projectId` int NOT NULL,
	`movieUrl` varchar(512),
	`movieKey` varchar(512),
	`duration` int,
	`status` enum('pending','assembling','completed','failed') NOT NULL DEFAULT 'pending',
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `finalMovies_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `generatedVideos` (
	`id` int AUTO_INCREMENT NOT NULL,
	`sceneId` int NOT NULL,
	`projectId` int NOT NULL,
	`videoUrl` varchar(512),
	`videoKey` varchar(512),
	`duration` int,
	`status` enum('pending','generating','completed','failed') NOT NULL DEFAULT 'pending',
	`errorMessage` text,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `generatedVideos_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `projects` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`title` varchar(255) NOT NULL,
	`description` text,
	`scriptContent` text NOT NULL,
	`status` enum('draft','parsing','parsed','generating_storyboard','generating_videos','assembling','completed','failed') NOT NULL DEFAULT 'draft',
	`progress` int NOT NULL DEFAULT 0,
	`errorMessage` text,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `projects_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `scenes` (
	`id` int AUTO_INCREMENT NOT NULL,
	`projectId` int NOT NULL,
	`sceneNumber` int NOT NULL,
	`title` varchar(255) NOT NULL,
	`description` text NOT NULL,
	`setting` varchar(255),
	`characters` text,
	`duration` int,
	`order` int NOT NULL,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `scenes_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `settings` (
	`id` int AUTO_INCREMENT NOT NULL,
	`projectId` int NOT NULL,
	`name` varchar(255) NOT NULL,
	`description` text NOT NULL,
	`visualDescription` text,
	`imageUrl` varchar(512),
	`imageKey` varchar(512),
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `settings_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `storyboardImages` (
	`id` int AUTO_INCREMENT NOT NULL,
	`sceneId` int NOT NULL,
	`projectId` int NOT NULL,
	`imageUrl` varchar(512) NOT NULL,
	`imageKey` varchar(512) NOT NULL,
	`prompt` text,
	`status` enum('pending','generating','completed','failed') NOT NULL DEFAULT 'pending',
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `storyboardImages_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `videoPrompts` (
	`id` int AUTO_INCREMENT NOT NULL,
	`sceneId` int NOT NULL,
	`projectId` int NOT NULL,
	`prompt` text NOT NULL,
	`duration` int,
	`style` varchar(255),
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `videoPrompts_id` PRIMARY KEY(`id`)
);
