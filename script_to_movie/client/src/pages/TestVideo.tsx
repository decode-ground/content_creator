import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { phase3Api } from "@/lib/api";
import { ArrowLeft, Upload, Video, Loader2, ImageIcon, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation } from "wouter";
import { toast } from "sonner";

const KLING_SUPPORTED = ["image/jpeg", "image/png", "image/webp"];

/** Convert any browser-renderable image to a JPEG File using Canvas. */
function convertToJpeg(file: File): Promise<File> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const objectUrl = URL.createObjectURL(file);

    img.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      const ctx = canvas.getContext("2d");
      if (!ctx) { reject(new Error("Canvas unavailable")); return; }
      ctx.drawImage(img, 0, 0);
      canvas.toBlob(
        (blob) => {
          URL.revokeObjectURL(objectUrl);
          if (!blob) { reject(new Error("Conversion failed")); return; }
          const jpegName = file.name.replace(/\.[^.]+$/, ".jpg");
          resolve(new File([blob], jpegName, { type: "image/jpeg" }));
        },
        "image/jpeg",
        0.92
      );
    };

    img.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error("Could not load image"));
    };

    img.src = objectUrl;
  });
}

type State =
  | { stage: "idle" }
  | { stage: "converting" }
  | { stage: "submitting" }
  | { stage: "polling"; attempts: number }
  | { stage: "done"; videoUrl: string; duration: number };

export default function TestVideo() {
  const [, setLocation] = useLocation();

  const [image, setImage] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [prompt, setPrompt] = useState("Cinematic motion, smooth camera movement, bring the scene to life with subtle animation");
  const [duration, setDuration] = useState<5 | 10>(5);
  const [isDragging, setIsDragging] = useState(false);
  const [state, setState] = useState<State>({ stage: "idle" });
  const [pollTaskId, setPollTaskId] = useState<string | null>(null);
  const [submittedDuration, setSubmittedDuration] = useState(5);

  const inputRef = useRef<HTMLInputElement>(null);

  // Poll Kling every 5 seconds while we have a task ID
  useEffect(() => {
    if (!pollTaskId) return;

    let cancelled = false;

    const doPoll = async () => {
      if (cancelled) return;
      try {
        const result = await phase3Api.pollImageToVideo(pollTaskId);
        if (cancelled) return;

        if (result.status === "completed" && result.video_url) {
          setPollTaskId(null);
          setState({ stage: "done", videoUrl: result.video_url, duration: submittedDuration });
          toast.success("Video generated!");
        } else if (result.status === "failed") {
          setPollTaskId(null);
          setState({ stage: "idle" });
          toast.error(`Kling failed: ${result.error || "Unknown error"}`);
        } else {
          setState((prev) =>
            prev.stage === "polling"
              ? { stage: "polling", attempts: prev.attempts + 1 }
              : prev
          );
        }
      } catch (err: any) {
        if (cancelled) return;
        setPollTaskId(null);
        setState({ stage: "idle" });
        toast.error(err?.message || "Polling failed");
      }
    };

    doPoll();
    const interval = setInterval(doPoll, 5000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [pollTaskId]);

  const setFile = useCallback(async (file: File) => {
    if (!file.type.startsWith("image/")) {
      toast.error("Please upload an image file");
      return;
    }

    // Show preview immediately from the original file
    setPreview(URL.createObjectURL(file));
    setState({ stage: "idle" });

    // If the format isn't supported by Kling, silently convert to JPEG
    if (!KLING_SUPPORTED.includes(file.type)) {
      setState({ stage: "converting" });
      toast.info(`Converting ${file.type.split("/")[1].toUpperCase()} → JPEG for Kling compatibility…`);
      try {
        const converted = await convertToJpeg(file);
        setImage(converted);
        toast.success("Converted to JPEG");
      } catch (e) {
        toast.error("Could not convert image — try saving it as JPEG first");
        setPreview(null);
      } finally {
        setState({ stage: "idle" });
      }
    } else {
      setImage(file);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) setFile(file);
    },
    [setFile]
  );

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) setFile(file);
    },
    [setFile]
  );

  const clearImage = () => {
    setImage(null);
    setPreview(null);
    setState({ stage: "idle" });
    setPollTaskId(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  const handleGenerate = async () => {
    if (!image) {
      toast.error("Please select an image first");
      return;
    }
    if (!prompt.trim()) {
      toast.error("Please enter a prompt");
      return;
    }

    setState({ stage: "submitting" });

    try {
      const result = await phase3Api.submitImageToVideo(image, prompt, duration);
      setSubmittedDuration(result.duration);
      setPollTaskId(result.task_id);
      setState({ stage: "polling", attempts: 0 });
      toast.info("Submitted to Kling — checking status every 5 seconds…");
    } catch (err: any) {
      setState({ stage: "idle" });
      toast.error(err?.message || "Submission failed");
    }
  };

  const isConverting = state.stage === "converting";
  const isSubmitting = state.stage === "submitting";
  const isPolling = state.stage === "polling";
  const isBusy = isConverting || isSubmitting || isPolling;
  const isDone = state.stage === "done";

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <div className="border-b border-slate-800/50 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-5 flex items-center gap-4">
          <Button
            variant="ghost"
            onClick={() => setLocation("/dashboard")}
            className="text-slate-400 hover:text-white"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Dashboard
          </Button>
          <div>
            <h1 className="text-xl font-bold text-white">Image → Video Test</h1>
            <p className="text-xs text-slate-400">Test Kling AI image-to-video generation</p>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 max-w-3xl space-y-6">
        {/* Drop Zone */}
        <Card className="border-slate-700 bg-gradient-to-br from-slate-800/50 to-slate-900/50">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <ImageIcon className="h-5 w-5 text-purple-400" />
              Storyboard Image
            </CardTitle>
            <CardDescription>Drop a scene image or click to browse</CardDescription>
          </CardHeader>
          <CardContent>
            {preview ? (
              <div className="relative rounded-lg overflow-hidden border border-slate-600">
                <img
                  src={preview}
                  alt="Selected"
                  className="w-full max-h-80 object-contain bg-slate-900"
                />
                <button
                  onClick={clearImage}
                  className="absolute top-2 right-2 bg-slate-900/80 hover:bg-slate-800 text-white rounded-full p-1 transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
                <div className="px-3 py-2 bg-slate-800/80 text-xs text-slate-400">
                  {image?.name} · {image ? (image.size / 1024).toFixed(0) : 0} KB
                </div>
              </div>
            ) : (
              <div
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
                onClick={() => inputRef.current?.click()}
                className={`
                  flex flex-col items-center justify-center gap-3 h-52 rounded-lg border-2 border-dashed
                  cursor-pointer transition-all
                  ${isDragging
                    ? "border-purple-500 bg-purple-500/10"
                    : "border-slate-600 hover:border-slate-500 hover:bg-slate-800/40"
                  }
                `}
              >
                <Upload className={`h-10 w-10 ${isDragging ? "text-purple-400" : "text-slate-500"}`} />
                <div className="text-center">
                  <p className="text-slate-300 font-medium">Drop image here</p>
                  <p className="text-slate-500 text-sm mt-1">or click to browse · JPEG, PNG, WebP, AVIF (auto-converted)</p>
                </div>
              </div>
            )}
            <input
              ref={inputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleFileChange}
            />
          </CardContent>
        </Card>

        {/* Prompt + Options */}
        <Card className="border-slate-700 bg-gradient-to-br from-slate-800/50 to-slate-900/50">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Video className="h-5 w-5 text-purple-400" />
              Generation Settings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Motion Prompt
              </label>
              <Textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe the camera movement and action…"
                className="bg-slate-900 border-slate-700 text-white placeholder-slate-500 min-h-24 resize-none"
              />
              <p className="text-xs text-slate-500 mt-1">
                Describe what motion to add — camera movement, character action, atmosphere
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Duration
              </label>
              <div className="flex gap-2">
                {([5, 10] as const).map((d) => (
                  <button
                    key={d}
                    onClick={() => setDuration(d)}
                    className={`
                      flex-1 py-2 rounded-lg border text-sm font-medium transition-all
                      ${duration === d
                        ? "border-purple-500 bg-purple-500/20 text-purple-300"
                        : "border-slate-600 bg-slate-800 text-slate-400 hover:border-slate-500"
                      }
                    `}
                  >
                    {d} seconds
                  </button>
                ))}
              </div>
            </div>

            <Button
              onClick={handleGenerate}
              disabled={isBusy || !image}
              className="w-full h-11 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white disabled:opacity-50"
            >
              {isConverting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Converting image…
                </>
              ) : isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Submitting to Kling…
                </>
              ) : isPolling ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating… ({state.stage === "polling" ? state.attempts * 5 : 0}s elapsed)
                </>
              ) : (
                <>
                  <Video className="mr-2 h-4 w-4" />
                  Generate Video
                </>
              )}
            </Button>

            {isPolling && (
              <p className="text-center text-xs text-slate-500">
                Kling is rendering your video — this page polls automatically every 5 seconds.
                You can safely leave and come back.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Result */}
        {isDone && state.stage === "done" && (
          <Card className="border-emerald-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Video className="h-5 w-5 text-emerald-400" />
                Generated Video
              </CardTitle>
              <CardDescription>{state.duration}s clip from Kling AI</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="aspect-video bg-black rounded-lg overflow-hidden">
                <video
                  src={state.videoUrl}
                  controls
                  autoPlay
                  className="w-full h-full"
                />
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={() => {
                    const a = document.createElement("a");
                    a.href = state.videoUrl;
                    a.download = "test_clip.mp4";
                    a.click();
                  }}
                  className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white"
                >
                  Download
                </Button>
                <Button
                  onClick={clearImage}
                  variant="outline"
                  className="flex-1 border-slate-700 text-slate-200 hover:bg-slate-800"
                >
                  Try Another
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
