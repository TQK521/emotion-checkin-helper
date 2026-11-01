import { describe, it, expect } from "vitest";
import { createEmptyData } from "./checkin";

describe("createEmptyData", () => {
  it("返回符合契约的空数据结构", () => {
    const data = createEmptyData();
    expect(data.start_date).toBeNull();
    expect(data.records).toEqual([]);
    expect(data.best_streak).toBe(0);
    expect(data.journal).toEqual([]);
    expect(data.custom_emotions).toEqual([]);
  });
});
