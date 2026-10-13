// One AudioContext at a time. iOS only lets audio start from a user gesture, so
// unlockAudio() is called from the Done tap; the rest-over alarm plays later.

let audioContext: AudioContext | null = null;

/**
 * Call from inside a tap. Starts a fresh context each time: on iOS a context
 * goes "interrupted" (not "suspended") when the app is backgrounded or another
 * app takes the audio, and after that it can stay silent even once it reports
 * "running" again. A new one made inside the gesture always plays.
 */
export function unlockAudio(): void {
  try {
    audioContext?.close().catch(() => {});
    audioContext = new AudioContext();
    audioContext.resume().catch(() => {});
  } catch (error) {
    console.log("Failed to initialize audio context:", error);
  }
}

async function readyContext(): Promise<AudioContext> {
  if (!audioContext || audioContext.state === "closed") audioContext = new AudioContext();
  if (audioContext.state !== "running") await audioContext.resume();
  return audioContext;
}

export async function playAlarm(): Promise<void> {
  try {
    const ctx = await readyContext();
    const oscillator = ctx.createOscillator();
    const gainNode = ctx.createGain();
    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);
    oscillator.frequency.value = 880; // A5
    oscillator.type = "square";

    // An insistent pattern: 5 beeps
    const beepDuration = 0.2;
    const beepGap = 0.15;
    for (let i = 0; i < 5; i++) {
      const startTime = ctx.currentTime + i * (beepDuration + beepGap);
      gainNode.gain.setValueAtTime(0.5, startTime);
      gainNode.gain.setValueAtTime(0, startTime + beepDuration);
    }
    oscillator.start();
    oscillator.stop(ctx.currentTime + 5 * (beepDuration + beepGap) + 0.1);
  } catch (error) {
    console.log("Web Audio API failed:", error);
    playFallbackSound();
  }
}

function playFallbackSound() {
  try {
    if (!audioContext) audioContext = new AudioContext();
    const ctx = audioContext;
    const duration = 0.2;
    const buffer = ctx.createBuffer(1, duration * ctx.sampleRate, ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < buffer.length; i++) {
      data[i] = Math.sin((2 * Math.PI * 880 * i) / ctx.sampleRate) * 0.5;
    }
    let playCount = 0;
    const playBeep = () => {
      const source = ctx.createBufferSource();
      source.buffer = buffer;
      source.connect(ctx.destination);
      source.start();
      if (++playCount < 5) setTimeout(playBeep, 350);
    };
    playBeep();
  } catch (error) {
    console.log("Fallback audio failed:", error);
  }
}

/** iOS Safari has no Vibration API; elsewhere this buzzes along with the alarm. */
export function vibrate(): void {
  if ("vibrate" in navigator) navigator.vibrate([200, 100, 200, 100, 200]);
}
