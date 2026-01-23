import { z } from "zod";
import { protectedProcedure, router } from "../_core/trpc";
import {
  createProject,
  getProjectById,
  getUserProjects,
  updateProjectStatus,
  createScene,
  getProjectScenes,
  createCharacter,
  getProjectCharacters,
  createSetting,
  getProjectSettings,
  createStoryboardImage,
  getProjectStoryboardImages,
  createVideoPrompt,
  getSceneVideoPrompt,
  createGeneratedVideo,
  getProjectGeneratedVideos,
  createFinalMovie,
  getProjectFinalMovie,
  updateCharacterImage,
  updateSettingImage,
} from "../db";
import {
  analyzeScript,
  generateStoryboardPrompt,
  generateVideoPrompt,
  validateSceneConsistency,
} from "../scriptAnalyzer";
import { generateSceneStoryboard, generateCharacterPortrait, generateSettingReference } from "../imageGenerator";

export const projectsRouter = router({
  // Create a new project
  create: protectedProcedure
    .input(
      z.object({
        title: z.string().min(1),
        description: z.string().optional(),
        scriptContent: z.string().min(1),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const result = await createProject(
        ctx.user.id,
        input.title,
        input.description || null,
        input.scriptContent
      );

      return { success: true, projectId: (result as any).insertId || 0 };
    }),

  // Get user's projects
  list: protectedProcedure.query(async ({ ctx }) => {
    return await getUserProjects(ctx.user.id);
  }),

  // Get project details
  get: protectedProcedure.input(z.object({ projectId: z.number() })).query(async ({ input }) => {
    return await getProjectById(input.projectId);
  }),

  // Parse script and extract scenes
  parseScript: protectedProcedure
    .input(z.object({ projectId: z.number() }))
    .mutation(async ({ input }) => {
      try {
        const project = await getProjectById(input.projectId);
        if (!project) {
          throw new Error("Project not found");
        }

        // Update status to parsing
        await updateProjectStatus(input.projectId, "parsing", 10);

        // Analyze the script
        const analysis = await analyzeScript(project.scriptContent);

        // Validate consistency
        const validation = validateSceneConsistency(analysis.scenes, analysis.characters, analysis.settings);
        if (!validation.isValid) {
          console.warn("Scene consistency issues:", validation.issues);
        }

        // Store scenes
        for (const scene of analysis.scenes) {
          await createScene(
            input.projectId,
            scene.sceneNumber,
            scene.title,
            scene.description,
            scene.setting,
            JSON.stringify(scene.characters),
            scene.order
          );
        }

        // Store characters
        for (const character of analysis.characters) {
          await createCharacter(
            input.projectId,
            character.name,
            character.description,
            character.visualDescription
          );
        }

        // Store settings
        for (const setting of analysis.settings) {
          await createSetting(
            input.projectId,
            setting.name,
            setting.description,
            setting.visualDescription
          );
        }

        // Update status to parsed
        await updateProjectStatus(input.projectId, "parsed", 30);

        return {
          success: true,
          analysis: {
            title: analysis.title,
            summary: analysis.summary,
            sceneCount: analysis.scenes.length,
            characterCount: analysis.characters.length,
            settingCount: analysis.settings.length,
            totalDuration: analysis.totalDuration,
            trailerScenes: analysis.trailerScenes,
          },
        };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "Unknown error";
        await updateProjectStatus(input.projectId, "failed", 0, errorMessage);
        throw error;
      }
    }),

  // Generate storyboards for all scenes
  generateStoryboards: protectedProcedure
    .input(z.object({ projectId: z.number() }))
    .mutation(async ({ input }) => {
      try {
        const project = await getProjectById(input.projectId);
        if (!project) {
          throw new Error("Project not found");
        }

        await updateProjectStatus(input.projectId, "generating_storyboard", 40);

        const scenes = await getProjectScenes(input.projectId);
        const characters = await getProjectCharacters(input.projectId);
        const settings = await getProjectSettings(input.projectId);

        const settingMap = new Map(settings.map((s) => [s.name, s]));
        const characterMap = new Map(characters.map((c) => [c.name, c]));

        let completed = 0;
        for (const scene of scenes) {
          try {
            const setting = settingMap.get(scene.setting || "");
            if (!setting) {
              console.warn(`Setting not found for scene ${scene.sceneNumber}`);
              continue;
            }

            const sceneCharacters = JSON.parse(scene.characters || "[]").map((name: string) =>
              characterMap.get(name)
            );

            const prompt = generateStoryboardPrompt(
              scene.description,
              { ...setting, visualDescription: setting.visualDescription || "", appearances: 1 },
              sceneCharacters.filter(Boolean).map((c: any) => ({ ...c, visualDescription: c.visualDescription || "", appearances: 1 }))
            );

            const { imageUrl, imageKey } = await generateSceneStoryboard(
              prompt,
              input.projectId,
              scene.id
            );

            await createStoryboardImage(scene.id, input.projectId, imageUrl, imageKey, prompt);

            completed++;
            const progress = 40 + Math.floor((completed / scenes.length) * 30);
            await updateProjectStatus(input.projectId, "generating_storyboard", progress);
          } catch (error) {
            console.error(`Error generating storyboard for scene ${scene.sceneNumber}:`, error);
          }
        }

        await updateProjectStatus(input.projectId, "generating_storyboard", 70);

        return {
          success: true,
          storyboardsGenerated: completed,
          totalScenes: scenes.length,
        };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "Unknown error";
        await updateProjectStatus(input.projectId, "failed", 0, errorMessage);
        throw error;
      }
    }),

  // Generate character portraits
  generateCharacterPortraits: protectedProcedure
    .input(z.object({ projectId: z.number() }))
    .mutation(async ({ input }) => {
      try {
        const characters = await getProjectCharacters(input.projectId);

        let completed = 0;
        for (const character of characters) {
          try {
            if (!character.visualDescription) {
              console.warn(`No visual description for character ${character.name}`);
              continue;
            }

            const visualDesc = character.visualDescription || "";
            const { imageUrl, imageKey } = await generateCharacterPortrait(
              character.name,
              visualDesc,
              input.projectId,
              character.id
            );

            await updateCharacterImage(character.id, imageUrl, imageKey);
            completed++;
          } catch (error) {
            console.error(`Error generating portrait for character ${character.name}:`, error);
          }
        }

        return {
          success: true,
          portraitsGenerated: completed,
          totalCharacters: characters.length,
        };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "Unknown error";
        throw error;
      }
    }),

  // Generate setting reference images
  generateSettingReferences: protectedProcedure
    .input(z.object({ projectId: z.number() }))
    .mutation(async ({ input }) => {
      try {
        const settings = await getProjectSettings(input.projectId);

        let completed = 0;
        for (const setting of settings) {
          try {
            if (!setting.visualDescription) {
              console.warn(`No visual description for setting ${setting.name}`);
              continue;
            }

            const visualDesc = setting.visualDescription || "";
            const { imageUrl, imageKey } = await generateSettingReference(
              setting.name,
              visualDesc,
              input.projectId,
              setting.id
            );

            await updateSettingImage(setting.id, imageUrl, imageKey);
            completed++;
          } catch (error) {
            console.error(`Error generating reference for setting ${setting.name}:`, error);
          }
        }

        return {
          success: true,
          referencesGenerated: completed,
          totalSettings: settings.length,
        };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "Unknown error";
        throw error;
      }
    }),

  // Get project scenes
  getScenes: protectedProcedure.input(z.object({ projectId: z.number() })).query(async ({ input }) => {
    return await getProjectScenes(input.projectId);
  }),

  // Get project characters
  getCharacters: protectedProcedure
    .input(z.object({ projectId: z.number() }))
    .query(async ({ input }) => {
      return await getProjectCharacters(input.projectId);
    }),

  // Get project settings
  getSettings: protectedProcedure.input(z.object({ projectId: z.number() })).query(async ({ input }) => {
    return await getProjectSettings(input.projectId);
  }),

  // Get storyboards
  getStoryboards: protectedProcedure
    .input(z.object({ projectId: z.number() }))
    .query(async ({ input }) => {
      return await getProjectStoryboardImages(input.projectId);
    }),

  // Get final movie
  getFinalMovie: protectedProcedure
    .input(z.object({ projectId: z.number() }))
    .query(async ({ input }) => {
      return await getProjectFinalMovie(input.projectId);
    }),
});
