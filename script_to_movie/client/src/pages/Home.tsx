import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { projectsApi } from "@/lib/api";
import { useMutation } from "@tanstack/react-query";
import { Film, Sparkles, Upload, ArrowRight, Play } from "lucide-react";
import { useLocation } from "wouter";
import { useState } from "react";
import { toast } from "sonner";

export default function Home() {
  const { user, isAuthenticated } = useAuth();
  const [, setLocation] = useLocation();
  const [isOpen, setIsOpen] = useState(false);
  const [formData, setFormData] = useState({ title: "", scriptContent: "" });

  const createProjectMutation = useMutation({
    mutationFn: projectsApi.create,
  });

  const handleCreateProject = async () => {
    if (!formData.title || !formData.scriptContent) {
      toast.error("Please fill in all required fields");
      return;
    }

    try {
      const result = await createProjectMutation.mutateAsync({
        title: formData.title,
        description: "",
        scriptContent: formData.scriptContent,
      });

      toast.success("Project created! Redirecting...");
      setIsOpen(false);
      setFormData({ title: "", scriptContent: "" });
      setLocation(`/project/${result.projectId}`);
    } catch (error) {
      toast.error("Failed to create project");
      console.error(error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Navigation */}
      <nav className="border-b border-slate-800/50 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <Film className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold text-white">Script to Movie</span>
          </div>
          <div className="flex items-center gap-4">
            {isAuthenticated ? (
              <>
                <span className="text-sm text-slate-400">{user?.name}</span>
                <Button
                  onClick={() => setLocation("/dashboard")}
                  variant="outline"
                  className="border-slate-700 text-slate-200 hover:bg-slate-800"
                >
                  Dashboard
                </Button>
              </>
            ) : (
              <Button onClick={() => setLocation("/dashboard")} className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700">
                Sign In
              </Button>
            )}
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-24">
        <div className="max-w-4xl mx-auto text-center">
          <div className="mb-6 inline-flex items-center gap-2 px-4 py-2 rounded-full bg-slate-800/50 border border-slate-700">
            <Sparkles className="w-4 h-4 text-purple-400" />
            <span className="text-sm text-slate-300">AI-Powered Video Production</span>
          </div>

          <h1 className="text-6xl md:text-7xl font-bold text-white mb-6 leading-tight">
            Script to
            <span className="bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 bg-clip-text text-transparent">
              {" "}Movie
            </span>
          </h1>

          <p className="text-xl text-slate-400 mb-12 max-w-2xl mx-auto">
            Transform your screenplay into a complete video production. Upload your script, see the storyboard, and watch your movie come to life.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            {isAuthenticated ? (
              <>
                <Dialog open={isOpen} onOpenChange={setIsOpen}>
                  <DialogTrigger asChild>
                    <Button className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white h-12 px-8 text-lg">
                      <Upload className="mr-2 h-5 w-5" />
                      Create Project
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="bg-slate-900 border-slate-700 max-w-2xl">
                    <DialogHeader>
                      <DialogTitle className="text-white">Create New Project</DialogTitle>
                      <DialogDescription>Upload your screenplay to get started</DialogDescription>
                    </DialogHeader>

                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-slate-200 mb-2">Project Title</label>
                        <Input
                          placeholder="e.g., The Last Adventure"
                          value={formData.title}
                          onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                          className="bg-slate-800 border-slate-700 text-white placeholder-slate-500"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-slate-200 mb-2">Screenplay</label>
                        <Textarea
                          placeholder="Paste your screenplay here..."
                          value={formData.scriptContent}
                          onChange={(e) => setFormData({ ...formData, scriptContent: e.target.value })}
                          className="bg-slate-800 border-slate-700 text-white placeholder-slate-500 min-h-64 font-mono text-sm"
                        />
                      </div>

                      <Button
                        onClick={handleCreateProject}
                        disabled={createProjectMutation.isPending}
                        className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white h-11"
                      >
                        {createProjectMutation.isPending ? "Creating..." : "Create Project"}
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>

                <Button
                  onClick={() => setLocation("/dashboard")}
                  variant="outline"
                  className="border-slate-700 text-slate-200 hover:bg-slate-800 h-12 px-8 text-lg"
                >
                  <ArrowRight className="mr-2 h-5 w-5" />
                  Go to Dashboard
                </Button>
              </>
            ) : (
              <Button onClick={() => setLocation("/dashboard")} className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white h-12 px-8 text-lg">
                <Play className="mr-2 h-5 w-5" />
                Get Started
              </Button>
            )}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="container mx-auto px-4 py-20 border-t border-slate-800">
        <h2 className="text-4xl font-bold text-white mb-12 text-center">How It Works</h2>

        <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          {[
            {
              step: "1",
              title: "Upload Script",
              description: "Paste your screenplay into the editor",
            },
            {
              step: "2",
              title: "View Storyboard",
              description: "See AI-generated visual scenes",
            },
            {
              step: "3",
              title: "Watch Movie",
              description: "Download your complete video",
            },
          ].map((item, i) => (
            <div key={i} className="text-center">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-white">{item.step}</span>
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">{item.title}</h3>
              <p className="text-slate-400">{item.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="container mx-auto px-4 py-20 border-t border-slate-800">
        <h2 className="text-4xl font-bold text-white mb-12 text-center">Powered by AI</h2>

        <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
          {[
            "Script Analysis & Scene Extraction",
            "Character Consistency Engine",
            "AI-Generated Storyboards",
            "Professional Video Synthesis",
            "Automatic Transitions & Assembly",
            "High-Quality Output",
          ].map((feature, i) => (
            <Card key={i} className="border-slate-700 bg-gradient-to-br from-slate-800/50 to-slate-900/50">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-gradient-to-r from-purple-400 to-pink-400" />
                  <p className="text-slate-300">{feature}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="container mx-auto px-4 py-20 border-t border-slate-800">
        <div className="max-w-2xl mx-auto text-center bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-slate-700 rounded-2xl p-12">
          <h2 className="text-3xl font-bold text-white mb-4">Ready to Create?</h2>
          <p className="text-slate-400 mb-8">Transform your screenplay into a stunning video with AI-powered production.</p>
          {isAuthenticated ? (
            <Dialog open={isOpen} onOpenChange={setIsOpen}>
              <DialogTrigger asChild>
                <Button className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white h-12 px-8 text-lg">
                  Create Your First Project
                </Button>
              </DialogTrigger>
            </Dialog>
          ) : (
            <Button onClick={() => setLocation("/dashboard")} className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white h-12 px-8 text-lg">
              Sign In to Get Started
            </Button>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-900/50 backdrop-blur-sm mt-20">
        <div className="container mx-auto px-4 py-8 text-center text-slate-500">
          <p>© 2026 Script to Movie. Powered by AI agents and advanced prompting.</p>
        </div>
      </footer>
    </div>
  );
}
