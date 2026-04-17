import { createFileRoute } from "@tanstack/react-router";
import { FileTranscriber } from "@/components/file-transcriber";

export const Route = createFileRoute("/transcribe")({
  component: TranscribePage,
});

function TranscribePage() {
  return <FileTranscriber />;
}
