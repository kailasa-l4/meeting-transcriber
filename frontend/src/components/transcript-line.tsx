const SPEAKER_COLORS = [
  "text-blue-400",
  "text-green-400",
  "text-yellow-400",
  "text-purple-400",
  "text-pink-400",
  "text-cyan-400",
];

interface TranscriptLineProps {
  speaker: number | null;
  text: string;
  isFinal: boolean;
}

export function TranscriptLine({ speaker, text, isFinal }: TranscriptLineProps) {
  const color = speaker !== null ? SPEAKER_COLORS[speaker % SPEAKER_COLORS.length] : "text-muted-foreground";

  return (
    <div className={`text-sm py-0.5 ${!isFinal ? "italic opacity-60" : ""}`}>
      {speaker !== null && (
        <span className={`font-medium ${color} mr-1`}>S{speaker}:</span>
      )}
      <span>{text}</span>
    </div>
  );
}
