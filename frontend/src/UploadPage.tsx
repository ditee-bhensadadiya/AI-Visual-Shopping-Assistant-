import { useEffect, useState, type FormEvent } from "react";
import { detectUpload, uploadImage, type DetectionRunResponse, type UploadResponse } from "./services/api";

const MAX_FILE_BYTES = 10 * 1024 * 1024;
const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];

function formatSize(bytes: number): string {
  return `${(bytes / (1024 * 1024)).toFixed(bytes < 1024 * 1024 ? 2 : 1)} MB`;
}

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState("");
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [detection, setDetection] = useState<DetectionRunResponse | null>(null);
  const [error, setError] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [isDetecting, setIsDetecting] = useState(false);

  useEffect(() => {
    if (!file) {
      setPreview("");
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  function chooseFile(next: File | undefined) {
    setError("");
    setResult(null);
    setDetection(null);
    if (!next) {
      setFile(null);
      return;
    }
    if (!ALLOWED_TYPES.includes(next.type)) {
      setFile(null);
      setError("Choose a JPEG, PNG, or WebP image.");
      return;
    }
    if (next.size > MAX_FILE_BYTES) {
      setFile(null);
      setError("The image must be 10 MB or smaller.");
      return;
    }
    setFile(next);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file || isUploading) return;
    setError("");
    setIsUploading(true);
    try {
      setResult(await uploadImage(file));
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "Upload failed. Please try again.");
    } finally {
      setIsUploading(false);
    }
  }

  async function runDetection() {
    if (!result || isDetecting || detection) return;
    setError("");
    setIsDetecting(true);
    try {
      const outcome = await detectUpload(result.id);
      setDetection(outcome);
      setResult((current) => current ? { ...current, processing_status: outcome.processing_status } : current);
    } catch (detectionError) {
      setError(detectionError instanceof Error ? detectionError.message : "Detection failed. Please try again.");
    } finally {
      setIsDetecting(false);
    }
  }

  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-10 sm:px-8 sm:py-16">
      <div className="mx-auto max-w-2xl">
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-emerald-800">Image upload and product analysis</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-stone-950 sm:text-4xl">Start with an image</h1>
        <p className="mt-4 leading-7 text-stone-600">Upload a product image, then use the local vision model to estimate product names, categories, and visible brands.</p>

        <form onSubmit={submit} className="mt-8 rounded-3xl border border-stone-200 bg-white p-5 shadow-sm sm:p-8">
          <label htmlFor="image-file" className="block text-sm font-semibold text-stone-900">Choose an image</label>
          <p id="image-help" className="mt-1 text-sm text-stone-500">JPEG, PNG, or WebP · up to 10 MB</p>
          <input
            id="image-file"
            aria-describedby="image-help"
            className="mt-4 block w-full cursor-pointer rounded-xl border border-stone-200 bg-stone-50 text-sm text-stone-700 file:mr-4 file:border-0 file:bg-emerald-900 file:px-4 file:py-3 file:font-semibold file:text-white hover:file:bg-emerald-800"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(event) => chooseFile(event.currentTarget.files?.[0])}
          />

          {file && (
            <div className="mt-6 grid gap-5 sm:grid-cols-[180px_1fr] sm:items-center">
              <img src={preview} alt="Selected image preview" className="aspect-square w-full rounded-2xl bg-stone-100 object-contain" />
              <div className="min-w-0">
                <p className="break-all font-medium text-stone-900">{file.name}</p>
                <p className="mt-1 text-sm text-stone-500">{formatSize(file.size)}</p>
              </div>
            </div>
          )}

          {error && <p role="alert" className="mt-5 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800">{error}</p>}

          <button
            type="submit"
            disabled={!file || isUploading}
            className="mt-6 rounded-full bg-emerald-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:bg-stone-300"
          >
            {isUploading ? "Uploading…" : result ? "Upload another image" : "Upload image"}
          </button>
        </form>

        {result && (
          <section aria-label="Uploaded image" className="mt-6 rounded-3xl border border-emerald-200 bg-emerald-50 p-5 sm:p-7">
            <p role="status" className="font-semibold text-emerald-950">Image uploaded · Status: {result.processing_status}</p>
            {detection ? (
              <div className="mt-4 overflow-hidden rounded-2xl bg-stone-950">
                <div className="relative mx-auto w-full" style={{ aspectRatio: `${detection.image_width} / ${detection.image_height}` }}>
                  <img src={result.image_url} alt="Uploaded image with detected objects" className="absolute inset-0 h-full w-full object-contain" />
                  <svg
                    aria-label="Detected object bounding boxes"
                    role="img"
                    viewBox={`0 0 ${detection.image_width} ${detection.image_height}`}
                    preserveAspectRatio="none"
                    className="absolute inset-0 h-full w-full"
                  >
                    {detection.detections.map((item, index) => (
                      <g key={item.id}>
                        <rect x={item.box.x1} y={item.box.y1} width={item.box.x2 - item.box.x1} height={item.box.y2 - item.box.y1} fill="rgba(16,185,129,0.08)" stroke="#10b981" strokeWidth={Math.max(2, detection.image_width / 400)} />
                        <text x={item.box.x1} y={Math.max(20, item.box.y1 - 6)} fill="white" fontSize={Math.max(16, detection.image_width / 45)} paintOrder="stroke" stroke="#064e3b" strokeWidth={Math.max(4, detection.image_width / 180)}>
                          {index + 1}. {item.class_name} · {Math.round(item.confidence * 100)}% estimate
                        </text>
                      </g>
                    ))}
                  </svg>
                </div>
                <div className="space-y-3 p-4" aria-label="Detection crops">
                  {detection.detections.length === 0 ? (
                    <p className="text-sm text-white">No products were recognized in this image. Try a clearer image with the product in focus.</p>
                  ) : detection.detections.map((item, index) => (
                    <div key={item.id} className="flex items-center gap-3 rounded-xl bg-white/10 p-3 text-white">
                      <img src={item.crop_url} alt={`${item.class_name} crop`} className="h-16 w-16 rounded-lg bg-white object-contain" />
                      <div className="text-sm">
                        <p className="font-semibold">{index + 1}. {item.class_name}</p>
                        <p className="mt-1 text-emerald-100">Brand: {item.brand ?? "Unknown"}</p>
                        <p className="text-emerald-100">Category: {item.category ?? "Unknown"}{item.color ? ` · ${item.color}` : ""}{item.model ? ` · ${item.model}` : ""}</p>
                        <p className="mt-1 text-xs text-emerald-200">
                          {item.brand_evidence === "visible_logo" ? "Brand based on a visible logo" : item.brand_evidence === "visible_text" ? "Brand based on visible text" : item.brand_evidence === "visual_style" ? "Brand is a visual estimate" : "Brand could not be confirmed"}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <img src={result.image_url} alt="Uploaded image" className="mt-4 max-h-[28rem] w-full rounded-2xl bg-white object-contain" />
            )}
            <p className="mt-3 break-all text-xs text-emerald-900">Upload ID: {result.id}</p>
            <p className="mt-1 text-xs text-emerald-900">Private preview link expires after one hour.</p>
            <p className="mt-2 text-xs text-emerald-900">Detection runs through Ollama on this computer, with no per-image AI API charge. The uploaded image is still stored in your Supabase project. Product and brand results can be uncertain.</p>
            <button
              type="button"
              onClick={runDetection}
              disabled={isDetecting || !!detection}
              className="mt-5 rounded-full bg-emerald-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:bg-stone-400"
            >
              {isDetecting ? "Detecting objects…" : detection ? `Detection complete · ${detection.detections.length} found` : "Detect products"}
            </button>
          </section>
        )}
      </div>
    </main>
  );
}
