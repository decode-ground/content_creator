import { int, mysqlEnum, mysqlTable, text, timestamp, varchar } from "drizzle-orm/mysql-core";

/**
 * Core user table backing auth flow.
 * Extend this file with additional tables as your product grows.
 * Columns use camelCase to match both database fields and generated types.
 */
export const users = mysqlTable("users", {
  /**
   * Surrogate primary key. Auto-incremented numeric value managed by the database.
   * Use this for relations between tables.
   */
  id: int("id").autoincrement().primaryKey(),
  /** User identifier - can be generated on registration or from external auth */
  openId: varchar("openId", { length: 64 }).notNull().unique(),
  name: text("name"),
  email: varchar("email", { length: 320 }).unique(),
  /** Hashed password for email/password authentication */
  passwordHash: varchar("passwordHash", { length: 255 }),
  loginMethod: varchar("loginMethod", { length: 64 }),
  role: mysqlEnum("role", ["user", "admin"]).default("user").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  lastSignedIn: timestamp("lastSignedIn").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

/**
 * Projects table - stores video production projects
 */
export const projects = mysqlTable("projects", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  title: varchar("title", { length: 255 }).notNull(),
  description: text("description"),
  scriptContent: text("scriptContent").notNull(),
  status: mysqlEnum("status", ["draft", "parsing", "parsed", "generating_storyboard", "generating_videos", "assembling", "completed", "failed"]).default("draft").notNull(),
  progress: int("progress").default(0).notNull(), // 0-100
  errorMessage: text("errorMessage"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type Project = typeof projects.$inferSelect;
export type InsertProject = typeof projects.$inferInsert;

/**
 * Characters table - stores character descriptions extracted from script
 */
export const characters = mysqlTable("characters", {
  id: int("id").autoincrement().primaryKey(),
  projectId: int("projectId").notNull(),
  name: varchar("name", { length: 255 }).notNull(),
  description: text("description").notNull(),
  visualDescription: text("visualDescription"), // For image generation
  imageUrl: varchar("imageUrl", { length: 512 }),
  imageKey: varchar("imageKey", { length: 512 }), // S3 key
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type Character = typeof characters.$inferSelect;
export type InsertCharacter = typeof characters.$inferInsert;

/**
 * Settings table - stores location/setting descriptions
 */
export const settings = mysqlTable("settings", {
  id: int("id").autoincrement().primaryKey(),
  projectId: int("projectId").notNull(),
  name: varchar("name", { length: 255 }).notNull(),
  description: text("description").notNull(),
  visualDescription: text("visualDescription"), // For image generation
  imageUrl: varchar("imageUrl", { length: 512 }),
  imageKey: varchar("imageKey", { length: 512 }), // S3 key
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type Setting = typeof settings.$inferSelect;
export type InsertSetting = typeof settings.$inferInsert;

/**
 * Scenes table - stores individual scenes from the script
 */
export const scenes = mysqlTable("scenes", {
  id: int("id").autoincrement().primaryKey(),
  projectId: int("projectId").notNull(),
  sceneNumber: int("sceneNumber").notNull(),
  title: varchar("title", { length: 255 }).notNull(),
  description: text("description").notNull(),
  setting: varchar("setting", { length: 255 }),
  characters: text("characters"), // JSON array of character names
  duration: int("duration"), // Estimated duration in seconds
  order: int("order").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type Scene = typeof scenes.$inferSelect;
export type InsertScene = typeof scenes.$inferInsert;

/**
 * Storyboard images table - stores generated still images for each scene
 */
export const storyboardImages = mysqlTable("storyboardImages", {
  id: int("id").autoincrement().primaryKey(),
  sceneId: int("sceneId").notNull(),
  projectId: int("projectId").notNull(),
  imageUrl: varchar("imageUrl", { length: 512 }).notNull(),
  imageKey: varchar("imageKey", { length: 512 }).notNull(), // S3 key
  prompt: text("prompt"), // The prompt used to generate this image
  status: mysqlEnum("status", ["pending", "generating", "completed", "failed"]).default("pending").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type StoryboardImage = typeof storyboardImages.$inferSelect;
export type InsertStoryboardImage = typeof storyboardImages.$inferInsert;

/**
 * Video prompts table - stores optimized prompts for video generation
 */
export const videoPrompts = mysqlTable("videoPrompts", {
  id: int("id").autoincrement().primaryKey(),
  sceneId: int("sceneId").notNull(),
  projectId: int("projectId").notNull(),
  prompt: text("prompt").notNull(),
  duration: int("duration"), // Desired video duration in seconds
  style: varchar("style", { length: 255 }), // Visual style guidance
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type VideoPrompt = typeof videoPrompts.$inferSelect;
export type InsertVideoPrompt = typeof videoPrompts.$inferInsert;

/**
 * Generated videos table - stores video file references and metadata
 */
export const generatedVideos = mysqlTable("generatedVideos", {
  id: int("id").autoincrement().primaryKey(),
  sceneId: int("sceneId").notNull(),
  projectId: int("projectId").notNull(),
  videoUrl: varchar("videoUrl", { length: 512 }),
  videoKey: varchar("videoKey", { length: 512 }), // S3 key
  duration: int("duration"), // Actual video duration in seconds
  status: mysqlEnum("status", ["pending", "generating", "completed", "failed"]).default("pending").notNull(),
  errorMessage: text("errorMessage"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type GeneratedVideo = typeof generatedVideos.$inferSelect;
export type InsertGeneratedVideo = typeof generatedVideos.$inferInsert;

/**
 * Final movies table - stores assembled movie files
 */
export const finalMovies = mysqlTable("finalMovies", {
  id: int("id").autoincrement().primaryKey(),
  projectId: int("projectId").notNull(),
  movieUrl: varchar("movieUrl", { length: 512 }),
  movieKey: varchar("movieKey", { length: 512 }), // S3 key
  duration: int("duration"), // Total movie duration in seconds
  status: mysqlEnum("status", ["pending", "assembling", "completed", "failed"]).default("pending").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type FinalMovie = typeof finalMovies.$inferSelect;
export type InsertFinalMovie = typeof finalMovies.$inferInsert;