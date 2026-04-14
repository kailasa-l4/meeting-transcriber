/**
 * Screen Wake Lock manager — prevents the screen from locking during recording.
 */

let wakeLock = null;

/**
 * Request a screen wake lock.
 * @returns {Promise<boolean>} true if acquired, false if not supported or failed
 */
export async function requestWakeLock() {
  if (!("wakeLock" in navigator)) {
    console.warn("Screen Wake Lock API not supported");
    return false;
  }

  try {
    wakeLock = await navigator.wakeLock.request("screen");

    wakeLock.addEventListener("release", () => {
      console.log("Wake lock released");
    });

    console.log("Wake lock acquired");
    return true;
  } catch (err) {
    console.error("Failed to acquire wake lock:", err);
    return false;
  }
}

/**
 * Release the screen wake lock.
 */
export async function releaseWakeLock() {
  if (wakeLock) {
    await wakeLock.release();
    wakeLock = null;
  }
}

/**
 * Re-acquire wake lock when the page becomes visible again.
 * Call this once during app initialization.
 */
export function setupVisibilityHandler() {
  document.addEventListener("visibilitychange", async () => {
    if (document.visibilityState === "visible" && wakeLock === null) {
      // Re-acquire only if we previously had it (i.e., recording is active)
      // The app.js will handle this by checking recording state
    }
  });
}

/**
 * Check if Wake Lock API is supported.
 */
export function isSupported() {
  return "wakeLock" in navigator;
}
