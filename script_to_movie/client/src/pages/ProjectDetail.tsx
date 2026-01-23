import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { trpc } from "@/lib/trpc";
import { ArrowLeft, Play, Images, Loader2 } from "lucide-react";
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

  const projectQuery = trpc.projects.get.useQuery({ projectId });
  const storyboardsQuery = trpc.projects.getStoryboards.useQuery({ projectId });
  const finalMovieQuery = trpc.projects.getFinalMovie.useQuery({ projectId });

  const startWorkflowMutation = trpc.workflow.startWorkflow.useMutation();

  // Load script content on mount
  useEffect(() => {
    if (projectQuery.data?.scriptContent) {
      setScriptContent(projectQuery.data.scriptContent);
    }
  }, [projectQuery.data]);

  // Auto-refresh storyboards and movie when processing
  useEffect(() => {
    if (!isProcessing) return;

    const interval = setInterval(() => {
      storyboardsQuery.refetch();
      finalMovieQuery.refetch();

      // Check if processing is complete
      if (storyboardsQuery.data?.length || finalMovieQuery.data?.movieUrl) {
        setIsProcessing(false);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [isProcessing, storyboardsQuery, finalMovieQuery]);

  const handleGenerateMovie = async () => {
    try {
      setIsProcessing(true);
      await startWorkflowMutation.mutateAsync({
        projectId,
        workflowType: "full_pipeline",
      });
      toast.success("Processing started! This may take a few minutes...");
      setActiveTab("storyboard");
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

  const hasStoryboards = storyboardsQuery.data && storyboardsQuery.data.length > 0;
  const hasMovie = finalMovieQuery.data?.movieUrl;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <div className="border-b border-slate-700/50 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-6">
          <Button onClick={() => setLocation("/dashboard")} variant="ghost" className="text-slate-400 hover:text-white mb-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <h1 className="text-4xl font-bold text-white">{project.title}</h1>
          {project.description && <p className="text-slate-400 mt-2">{project.description}</p>}
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="bg-slate-800 border-slate-700 w-full justify-start">
            <TabsTrigger value="input" className="text-slate-400 data-[state=active]:text-white">
              Script
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
                  <p className="text-slate-400">Generate a movie to see the storyboard</p>
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
                  <p className="text-slate-400">Generate a movie to watch it here</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
