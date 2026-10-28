// Web Worker for the muhurta search: loads the engine once, then runs whole
// days on request (see startSearch in muhurta-search.js).
import { initEngine } from './engine.js';
import { processDay } from './muhurta-search.js';

const ready = initEngine();

self.onmessage = async ({ data: task }) => {
  await ready;
  try {
    const { results, fetchErrors } = processDay(task);
    self.postMessage({ day: task.day, results, fetchErrors });
  } catch (e) {
    self.postMessage({ day: task.day, error: String(e) });
  }
};
