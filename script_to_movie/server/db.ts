import { eq } from "drizzle-orm";
import { drizzle } from "drizzle-orm/mysql2";
import { InsertUser, users, projects, scenes, characters, settings, storyboardImages, videoPrompts, generatedVideos, finalMovies } from "../drizzle/schema";

let _db: ReturnType<typeof drizzle> | null = null;

// Lazily create the drizzle instance so local tooling can run without a DB.
export async function getDb() {
  if (!_db && process.env.DATABASE_URL) {
    try {
      _db = drizzle(process.env.DATABASE_URL);
    } catch (error) {
      console.warn("[Database] Failed to connect:", error);
      _db = null;
    }
  }
  return _db;
}

export async function upsertUser(user: InsertUser): Promise<void> {
  if (!user.openId) {
    throw new Error("User openId is required for upsert");
  }

  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot upsert user: database not available");
    return;
  }

  try {
    const values: InsertUser = {
      openId: user.openId,
    };
    const updateSet: Record<string, unknown> = {};

    const textFields = ["name", "email", "loginMethod"] as const;
    type TextField = (typeof textFields)[number];

    const assignNullable = (field: TextField) => {
      const value = user[field];
      if (value === undefined) return;
      const normalized = value ?? null;
      values[field] = normalized;
      updateSet[field] = normalized;
    };

    textFields.forEach(assignNullable);

    if (user.lastSignedIn !== undefined) {
      values.lastSignedIn = user.lastSignedIn;
      updateSet.lastSignedIn = user.lastSignedIn;
    }
    if (user.role !== undefined) {
      values.role = user.role;
      updateSet.role = user.role;
    }

    if (!values.lastSignedIn) {
      values.lastSignedIn = new Date();
    }

    if (Object.keys(updateSet).length === 0) {
      updateSet.lastSignedIn = new Date();
    }

    await db.insert(users).values(values).onDuplicateKeyUpdate({
      set: updateSet,
    });
  } catch (error) {
    console.error("[Database] Failed to upsert user:", error);
    throw error;
  }
}

export async function getUserByOpenId(openId: string) {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot get user: database not available");
    return undefined;
  }

  const result = await db.select().from(users).where(eq(users.openId, openId)).limit(1);

  return result.length > 0 ? result[0] : undefined;
}

// Project queries
export async function createProject(userId: number, title: string, description: string | null, scriptContent: string) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  const result = await db.insert(projects).values({
    userId,
    title,
    description,
    scriptContent,
    status: 'draft',
  });
  
  return result;
}

export async function getProjectById(projectId: number) {
  const db = await getDb();
  if (!db) return undefined;
  
  const result = await db.select().from(projects).where(eq(projects.id, projectId)).limit(1);
  return result.length > 0 ? result[0] : undefined;
}

export async function getUserProjects(userId: number) {
  const db = await getDb();
  if (!db) return [];
  
  return await db.select().from(projects).where(eq(projects.userId, userId)).orderBy(projects.createdAt);
}

export async function updateProjectStatus(projectId: number, status: string, progress: number = 0, errorMessage: string | null = null) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  return await db.update(projects).set({
    status: status as any,
    progress,
    errorMessage,
    updatedAt: new Date(),
  }).where(eq(projects.id, projectId));
}

// Scene queries
export async function createScene(projectId: number, sceneNumber: number, title: string, description: string, setting: string | null, characters: string, order: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  return await db.insert(scenes).values({
    projectId,
    sceneNumber,
    title,
    description,
    setting,
    characters,
    order,
  });
}

export async function getProjectScenes(projectId: number) {
  const db = await getDb();
  if (!db) return [];
  
  return await db.select().from(scenes).where(eq(scenes.projectId, projectId)).orderBy(scenes.order);
}

// Character queries
export async function createCharacter(projectId: number, name: string, description: string, visualDescription: string | null = null) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  return await db.insert(characters).values({
    projectId,
    name,
    description,
    visualDescription,
  });
}

export async function getProjectCharacters(projectId: number) {
  const db = await getDb();
  if (!db) return [];
  
  return await db.select().from(characters).where(eq(characters.projectId, projectId));
}

export async function updateCharacterImage(characterId: number, imageUrl: string, imageKey: string) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  return await db.update(characters).set({
    imageUrl,
    imageKey,
    updatedAt: new Date(),
  }).where(eq(characters.id, characterId));
}

// Setting queries
export async function createSetting(projectId: number, name: string, description: string, visualDescription: string | null = null) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  return await db.insert(settings).values({
    projectId,
    name,
    description,
    visualDescription,
  });
}

export async function getProjectSettings(projectId: number) {
  const db = await getDb();
  if (!db) return [];
  
  return await db.select().from(settings).where(eq(settings.projectId, projectId));
}

export async function updateSettingImage(settingId: number, imageUrl: string, imageKey: string) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  return await db.update(settings).set({
    imageUrl,
    imageKey,
    updatedAt: new Date(),
  }).where(eq(settings.id, settingId));
}

// Storyboard image queries
export async function createStoryboardImage(sceneId: number, projectId: number, imageUrl: string, imageKey: string, prompt: string | null = null) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  return await db.insert(storyboardImages).values({
    sceneId,
    projectId,
    imageUrl,
    imageKey,
    prompt,
    status: 'completed',
  });
}

export async function getSceneStoryboardImage(sceneId: number) {
  const db = await getDb();
  if (!db) return undefined;
  
  const result = await db.select().from(storyboardImages).where(eq(storyboardImages.sceneId, sceneId)).limit(1);
  return result.length > 0 ? result[0] : undefined;
}

export async function getProjectStoryboardImages(projectId: number) {
  const db = await getDb();
  if (!db) return [];
  
  return await db.select().from(storyboardImages).where(eq(storyboardImages.projectId, projectId)).orderBy(storyboardImages.createdAt);
}

// Video prompt queries
export async function createVideoPrompt(sceneId: number, projectId: number, prompt: string, duration: number | null = null, style: string | null = null) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  return await db.insert(videoPrompts).values({
    sceneId,
    projectId,
    prompt,
    duration,
    style,
  });
}

export async function getSceneVideoPrompt(sceneId: number) {
  const db = await getDb();
  if (!db) return undefined;
  
  const result = await db.select().from(videoPrompts).where(eq(videoPrompts.sceneId, sceneId)).limit(1);
  return result.length > 0 ? result[0] : undefined;
}

// Generated video queries
export async function createGeneratedVideo(sceneId: number, projectId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  return await db.insert(generatedVideos).values({
    sceneId,
    projectId,
    status: 'pending',
  });
}

export async function updateGeneratedVideo(videoId: number, videoUrl: string | null, videoKey: string | null, duration: number | null, status: string, errorMessage: string | null = null) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  return await db.update(generatedVideos).set({
    videoUrl,
    videoKey,
    duration,
    status: status as any,
    errorMessage,
    updatedAt: new Date(),
  }).where(eq(generatedVideos.id, videoId));
}

export async function getProjectGeneratedVideos(projectId: number) {
  const db = await getDb();
  if (!db) return [];
  
  return await db.select().from(generatedVideos).where(eq(generatedVideos.projectId, projectId)).orderBy(generatedVideos.createdAt);
}

// Final movie queries
export async function createFinalMovie(projectId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  return await db.insert(finalMovies).values({
    projectId,
    status: 'pending',
  });
}

export async function updateFinalMovie(movieId: number, movieUrl: string | null, movieKey: string | null, duration: number | null, status: string) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  return await db.update(finalMovies).set({
    movieUrl,
    movieKey,
    duration,
    status: status as any,
    updatedAt: new Date(),
  }).where(eq(finalMovies.id, movieId));
}

export async function getProjectFinalMovie(projectId: number) {
  const db = await getDb();
  if (!db) return undefined;
  
  const result = await db.select().from(finalMovies).where(eq(finalMovies.projectId, projectId)).limit(1);
  return result.length > 0 ? result[0] : undefined;
}

// Re-export types for use in routers
export type { Project, InsertProject, Scene, InsertScene, Character, InsertCharacter, Setting, InsertSetting, StoryboardImage, InsertStoryboardImage, VideoPrompt, InsertVideoPrompt, GeneratedVideo, InsertGeneratedVideo, FinalMovie, InsertFinalMovie } from "../drizzle/schema";
