import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { projectsApi, workflowApi } from "@/lib/api";
import { useQuery, useMutation } from "@tanstack/react-query";
import { ArrowLeft, Play, Images, Loader2, Users, MapPin, Film, FileText } from "lucide-react";
import { useLocation, useRoute } from "wouter";
import { toast } from "sonner";
import { useState, useEffect } from "react";

export default function ProjectDetail() {
  const [, params] = useRoute("/project/:id");
  const [, setLocation] = useLocation();
  const projectId = params?.id ? parseInt(params.id) : 0;

  const [activeTab, setActiveTab] = useState("input");
  const [scriptContent, setScriptContent] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);

  const projectQuery = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => projectsApi.get(projectId),
    enabled: projectId > 0,
  });

  const scenesQuery = useQuery({
    queryKey: ["scenes", projectId],
    queryFn: () => projectsApi.getScenes(projectId),
    enabled: projectId > 0,
  });

  const charactersQuery = useQuery({
    queryKey: ["characters", projectId],
    queryFn: () => projectsApi.getCharacters(projectId),
    enabled: projectId > 0,
  });

  const settingsQuery = useQuery({
    queryKey: ["settings", projectId],
    queryFn: () => projectsApi.getSettings(projectId),
    enabled: projectId > 0,
  });

  const storyboardsQuery = useQuery({
    queryKey: ["storyboards", projectId],
    queryFn: () => projectsApi.getStoryboards(projectId),
    enabled: projectId > 0,
  });

  const finalMovieQuery = useQuery({
    queryKey: ["finalMovie", projectId],
    queryFn: () => projectsApi.getFinalMovie(projectId),
    enabled: projectId > 0,
  });

  const startWorkflowMutation = useMutation({
    mutationFn: ({ projectId, workflowType }: { projectId: number; workflowType: string }) =>
      workflowApi.start(projectId, workflowType),
  });

  // Load script content on mount
  useEffect(() => {
    if (projectQuery.data?.scriptContent) {
      setScriptContent(projectQuery.data.scriptContent);
    }
  }, [projectQuery.data]);

  // Auto-refresh when processing
  useEffect(() => {
    if (!isProcessing) return;

    const interval = setInterval(() => {
      projectQuery.refetch();
      scenesQuery.refetch();
      charactersQuery.refetch();
      settingsQuery.refetch();
      storyboardsQuery.refetch();
      finalMovieQuery.refetch();

      // Check if processing is complete
      const status = projectQuery.data?.status;
      if (status === "completed" || status === "parsed" || status === "failed") {
        setIsProcessing(false);
        if (status === "completed" || status === "parsed") {
          toast.success("Processing complete!");
          setActiveTab("scenes");
        } else if (status === "failed") {
          toast.error("Processing failed: " + (projectQuery.data?.errorMessage || "Unknown error"));
        }
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [isProcessing, projectQuery, scenesQuery, charactersQuery, settingsQuery, storyboardsQuery, finalMovieQuery]);

  const handleGenerateMovie = async () => {
    try {
      setIsProcessing(true);
      await startWorkflowMutation.mutateAsync({
        projectId,
        workflowType: "full_pipeline",
      });
      toast.success("Processing started! This may take a few minutes...");
    } catch (error) {
      setIsProcessing(false);
      toast.error("Failed to start processing");
      console.error(error);
    }
  };

  if (projectQuery.isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
      </div>
    );
  }

  const project = projectQuery.data;
  if (!project) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="container mx-auto px-4 py-8">
          <Button onClick={() => setLocation("/dashboard")} variant="ghost" className="text-white">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Projects
          </Button>
          <p className="text-white mt-8">Project not found</p>
        </div>
      </div>
    );
  }

  const scenes = scenesQuery.data || [];
  const characters = charactersQuery.data || [];
  const settings = settingsQuery.data || [];
  const hasScenes = scenes.length > 0;
  const hasStoryboards = storyboardsQuery.data && storyboardsQuery.data.length > 0;
  const hasMovie = finalMovieQuery.data?.movieUrl;

  // Status badge
  const statusColors: Record<string, string> = {
    draft: "bg-slate-600",
    parsing: "bg-yellow-600",
    parsed: "bg-green-600",
    generating_videos: "bg-blue-600",
    completed: "bg-emerald-600",
    failed: "bg-red-600",
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <div className="border-b border-slate-700/50 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-6">
          <Button onClick={() => setLocation("/dashboard")} variant="ghost" className="text-slate-400 hover:text-white mb-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <div className="flex items-center gap-4">
            <h1 className="text-4xl font-bold text-white">{project.title}</h1>
            <span className={`px-3 py-1 rounded-full text-xs font-medium text-white ${statusColors[project.status] || "bg-slate-600"}`}>
              {project.status}
            </span>
            {project.progress > 0 && project.progress < 100 && (
              <span className="text-sm text-slate-400">{project.progress}%</span>
            )}
          </div>
          {project.description && <p className="text-slate-400 mt-2">{project.description}</p>}
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="bg-slate-800 border-slate-700 w-full justify-start flex-wrap">
            <TabsTrigger value="input" className="text-slate-400 data-[state=active]:text-white">
              <FileText className="mr-2 h-4 w-4" />
              Script
            </TabsTrigger>
            <TabsTrigger value="scenes" className="text-slate-400 data-[state=active]:text-white">
              <Film className="mr-2 h-4 w-4" />
              Scenes {hasScenes && <span className="ml-1 text-xs opacity-70">({scenes.length})</span>}
            </TabsTrigger>
            <TabsTrigger value="characters" className="text-slate-400 data-[state=active]:text-white">
              <Users className="mr-2 h-4 w-4" />
              Characters {characters.length > 0 && <span className="ml-1 text-xs opacity-70">({characters.length})</span>}
            </TabsTrigger>
            <TabsTrigger value="settings" className="text-slate-400 data-[state=active]:text-white">
              <MapPin className="mr-2 h-4 w-4" />
              Settings {settings.length > 0 && <span className="ml-1 text-xs opacity-70">({settings.length})</span>}
            </TabsTrigger>
            <TabsTrigger value="storyboard" className="text-slate-400 data-[state=active]:text-white">
              <Images className="mr-2 h-4 w-4" />
              Storyboard
            </TabsTrigger>
            <TabsTrigger value="movie" className="text-slate-400 data-[state=active]:text-white">
              <Play className="mr-2 h-4 w-4" />
              Movie
            </TabsTrigger>
          </TabsList>

          {/* Script Input Tab */}
          <TabsContent value="input" className="space-y-6">
            <Card className="border-slate-700 bg-gradient-to-br from-slate-800/50 to-slate-900/50">
              <CardHeader>
                <CardTitle className="text-white">Your Screenplay</CardTitle>
                <CardDescription>Edit your script or paste a new one to generate a movie</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Textarea
                  value={scriptContent}
                  onChange={(e) => setScriptContent(e.target.value)}
                  placeholder="Paste your screenplay here..."
                  className="bg-slate-900 border-slate-700 text-white placeholder-slate-500 min-h-96 font-mono text-sm"
                />

                <Button
                  onClick={handleGenerateMovie}
                  disabled={isProcessing || !scriptContent.trim()}
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white h-12 text-lg"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Play className="mr-2 h-5 w-5" />
                      Generate Movie
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Scenes Tab */}
          <TabsContent value="scenes" className="space-y-6">
            {isProcessing && !hasScenes && (
              <Card className="border-slate-700 bg-gradient-to-br from-slate-800/50 to-slate-900/50">
                <CardContent className="py-12 text-center">
                  <Loader2 className="w-8 h-8 text-purple-500 animate-spin mx-auto mb-4" />
                  <p className="text-slate-300 mb-2">Analyzing script...</p>
                  <p className="text-sm text-slate-500">Extracting scenes, characters, and settings</p>
                </CardContent>
              </Card>
            )}

            {hasScenes ? (
              <div className="space-y-4">
                <p className="text-sm text-slate-400">{scenes.length} scenes extracted from your screenplay</p>
                {scenes.map((scene) => (
                  <Card key={scene.id} className="border-slate-700 bg-gradient-to-br from-slate-800/50 to-slate-900/50">
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-white text-lg">
                          Scene {scene.sceneNumber}: {scene.title}
                        </CardTitle>
                        <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded">
                          {scene.duration || "—"}s
                        </span>
                      </div>
                      {scene.setting && (
                        <div className="flex items-center gap-1 text-sm text-purple-400">
                          <MapPin className="h-3 w-3" />
                          {scene.setting}
                        </div>
                      )}
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <p className="text-slate-300 text-sm leading-relaxed">{scene.description}</p>
                      {scene.characters && (
                        <div className="flex flex-wrap gap-2">
                          {JSON.parse(scene.characters).map((name: string) => (
                            <span key={name} className="text-xs bg-slate-700 text-slate-300 px-2 py-1 rounded-full">
                              {name}
                            </span>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : !isProcessing ? (
              <Card className="border-slate-700 bg-gradient-to-br from-slate-800/50 to-slate-900/50">
                <CardContent className="py-12 text-center">
                  <Film className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                  <p className="text-slate-400">Click "Generate Movie" to analyze your script</p>
                </CardContent>
              </Card>
            ) : null}
          </TabsContent>

          {/* Characters Tab */}
          <TabsContent value="characters" className="space-y-6">
            {characters.length > 0 ? (
              <div className="space-y-4">
                <p className="text-sm text-slate-400">{characters.length} characters identified</p>
                <div className="grid gap-4 md:grid-cols-2">
                  {characters.map((char) => (
                    <Card key={char.id} className="border-slate-700 bg-gradient-to-br from-slate-800/50 to-slate-900/50">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-white text-lg flex items-center gap-2">
                          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-sm font-bold text-white">
                            {char.name.charAt(0)}
                          </div>
                          {char.name}
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        <p className="text-slate-300 text-sm">{char.description}</p>
                        {char.visualDescription && (
                          <div className="border-t border-slate-700 pt-2 mt-2">
                            <p className="text-xs text-slate-500 mb-1">Visual Description</p>
                            <p className="text-slate-400 text-sm italic">{char.visualDescription}</p>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            ) : (
              <Card className="border-slate-700 bg-gradient-to-br from-slate-800/50 to-slate-900/50">
                <CardContent className="py-12 text-center">
                  <Users className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                  <p className="text-slate-400">Characters will appear after script analysis</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            {settings.length > 0 ? (
              <div className="space-y-4">
                <p className="text-sm text-slate-400">{settings.length} locations/settings identified</p>
                <div className="grid gap-4 md:grid-cols-2">
                  {settings.map((setting) => (
                    <Card key={setting.id} className="border-slate-700 bg-gradient-to-br from-slate-800/50 to-slate-900/50">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-white text-lg flex items-center gap-2">
                          <MapPin className="h-5 w-5 text-purple-400" />
                          {setting.name}
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        <p className="text-slate-300 text-sm">{setting.description}</p>
                        {setting.visualDescription && (
                          <div className="border-t border-slate-700 pt-2 mt-2">
                            <p className="text-xs text-slate-500 mb-1">Visual Description</p>
                            <p className="text-slate-400 text-sm italic">{setting.visualDescription}</p>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            ) : (
              <Card className="border-slate-700 bg-gradient-to-br from-slate-800/50 to-slate-900/50">
                <CardContent className="py-12 text-center">
                  <MapPin className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                  <p className="text-slate-400">Settings/locations will appear after script analysis</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Storyboard Tab */}
          <TabsContent value="storyboard" className="space-y-6">
            {isProcessing && !hasStoryboards && (
              <Card className="border-slate-700 bg-gradient-to-br from-slate-800/50 to-slate-900/50">
                <CardContent className="py-12 text-center">
                  <Loader2 className="w-8 h-8 text-purple-500 animate-spin mx-auto mb-4" />
                  <p className="text-slate-300 mb-2">Generating storyboard...</p>
                  <p className="text-sm text-slate-500">This may take a few minutes</p>
                </CardContent>
              </Card>
            )}

            {hasStoryboards ? (
              <div className="space-y-4">
                <div className="text-sm text-slate-400">
                  {storyboardsQuery.data?.length} scenes generated
                </div>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {storyboardsQuery.data?.map((image, index) => (
                    <Card key={image.id} className="border-slate-700 bg-slate-800 overflow-hidden hover:border-slate-600 transition-colors">
                      <div className="relative h-56 bg-slate-700 overflow-hidden group">
                        <img
                          src={image.imageUrl}
                          alt={`Scene ${image.sceneId}`}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                      </div>
                      <CardContent className="pt-4">
                        <p className="text-sm font-medium text-white">Scene {index + 1}</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            ) : (
              <Card className="border-slate-700 bg-gradient-to-br from-slate-800/50 to-slate-900/50">
                <CardContent className="py-12 text-center">
                  <Images className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                  <p className="text-slate-400">Storyboard will be generated in a later phase</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Movie Tab */}
          <TabsContent value="movie" className="space-y-6">
            {isProcessing && !hasMovie && (
              <Card className="border-slate-700 bg-gradient-to-br from-slate-800/50 to-slate-900/50">
                <CardContent className="py-12 text-center">
                  <Loader2 className="w-8 h-8 text-purple-500 animate-spin mx-auto mb-4" />
                  <p className="text-slate-300 mb-2">Generating your movie...</p>
                  <p className="text-sm text-slate-500">This may take several minutes</p>
                </CardContent>
              </Card>
            )}

            {hasMovie && finalMovieQuery.data ? (
              <Card className="border-slate-700 bg-gradient-to-br from-slate-800/50 to-slate-900/50 overflow-hidden">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Play className="h-5 w-5" />
                    Your Movie
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="aspect-video bg-black rounded-lg overflow-hidden">
                    <video
                      src={finalMovieQuery.data.movieUrl || ""}
                      controls
                      className="w-full h-full"
                      controlsList="nodownload"
                    />
                  </div>
                  <div className="mt-4 flex gap-2">
                    <Button
                      onClick={() => {
                        const a = document.createElement("a");
                        a.href = finalMovieQuery.data?.movieUrl || "";
                        a.download = `${project.title}.mp4`;
                        a.click();
                      }}
                      className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white"
                    >
                      Download Movie
                    </Button>
                    <Button
                      onClick={() => setActiveTab("input")}
                      variant="outline"
                      className="flex-1 border-slate-700 text-slate-200 hover:bg-slate-800"
                    >
                      Edit Script
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card className="border-slate-700 bg-gradient-to-br from-slate-800/50 to-slate-900/50">
                <CardContent className="py-12 text-center">
                  <Play className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                  <p className="text-slate-400">Movie will be assembled in the final phase</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
