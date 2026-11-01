<script setup lang="ts">
// BreathGuideModal —— 四呼吸引导弹窗（对齐 pages_tool.py BreathingDialog）
// 定时器驱动：1s tick 推进阶段/倒计时；圆的缩放由 CSS transition 平滑过渡。
import { computed, onUnmounted, ref, watch } from "vue";
import BaseModal from "@/shared/ui/BaseModal.vue";
import {
  BREATH_MODES,
  buildBreathPlan,
  type BreathMode,
} from "./tool-data";

const props = defineProps<{
  open: boolean;
  mode: BreathMode;
}>();

const emit = defineEmits<{ close: [] }>();

const spec = computed(() => BREATH_MODES[props.mode]);
const plan = computed(() => buildBreathPlan(spec.value));

let timer: ReturnType<typeof setInterval> | null = null;
const planIdx = ref(0);
const elapsed = ref(0);
const running = ref(false);
const finished = ref(false);

const current = computed(() => plan.value[Math.min(planIdx.value, plan.value.length - 1)]);
/** 倒计时秒数（对齐旧版 ceil 口径：阶段内显示 dur - elapsed，最小 1） */
const countText = computed(() => {
  if (!running.value && finished.value) return "感谢你的这几分钟";
  if (!running.value) return "";
  return String(Math.max(1, current.value.phase.dur - elapsed.value));
});
const phaseText = computed(() => {
  if (finished.value) return "完成 ✓";
  if (!running.value) return "准备就绪";
  return `第 ${current.value.round} 轮 · ${current.value.phase.name}`;
});
const roundText = computed(() =>
  running.value ? `第 ${current.value.round}/${spec.value.rounds} 轮` : "",
);

/** 圆缩放：吸气类放大、呼气类缩小、屏息保持（CSS transition 平滑） */
const circleStyle = computed(() => {
  const pname = running.value && !finished.value ? current.value.phase.name : "";
  const inhale = pname === "吸气" || pname === "快吸" || pname === "补吸";
  const exhale = pname === "呼气" || pname === "长呼";
  const scale = finished.value || !running.value ? 0.82 : inhale ? 1.18 : exhale ? 0.82 : 1.18;
  return {
    transform: `scale(${scale})`,
    transitionDuration: inhale || exhale ? `${current.value.phase.dur}s` : "0.3s",
  };
});

function clearTimer(): void {
  if (timer !== null) {
    clearInterval(timer);
    timer = null;
  }
}

function start(): void {
  clearTimer();
  planIdx.value = 0;
  elapsed.value = 0;
  finished.value = false;
  running.value = true;
  timer = setInterval(tick, 1000);
}

function stop(): void {
  running.value = false;
  finished.value = false;
  clearTimer();
  planIdx.value = 0;
  elapsed.value = 0;
}

function finish(): void {
  running.value = false;
  finished.value = true;
  clearTimer();
}

function tick(): void {
  if (!running.value) return;
  elapsed.value += 1;
  if (elapsed.value >= current.value.phase.dur) {
    planIdx.value += 1;
    elapsed.value = 0;
    if (planIdx.value >= plan.value.length) {
      finish();
    }
  }
}

// 弹窗关闭（含点遮罩/×）时必须清定时器
watch(
  () => props.open,
  (v) => {
    if (!v) stop();
  },
);

onUnmounted(clearTimer);
</script>

<template>
  <BaseModal :open="open" :title="spec.title" @close="emit('close')">
    <div data-test="breath-modal">
      <p class="breath-desc">{{ spec.desc }}</p>
      <div class="breath-stage">
        <div class="breath-circle" data-test="breath-circle" :style="circleStyle"></div>
      </div>
      <p class="breath-phase" data-test="breath-phase">{{ phaseText }}</p>
      <p class="breath-count" data-test="breath-count">{{ countText }}</p>
      <p class="breath-round" data-test="breath-round">{{ roundText }}</p>
      <div class="breath-btns">
        <button type="button" class="btn-primary" data-test="breath-start" @click="start">
          {{ finished ? "再来一轮" : running ? "重来" : "开始" }}
        </button>
        <button type="button" class="btn-soft" data-test="breath-stop" @click="stop">停止</button>
      </div>
    </div>
  </BaseModal>
</template>

<style scoped>
.breath-desc {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--col-sub);
  text-align: center;
}

.breath-stage {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 220px;
}

.breath-circle {
  width: 140px;
  height: 140px;
  border-radius: 50%;
  background: var(--col-soft);
  border: 3px solid var(--col-primary);
  transform: scale(0.82);
  transition: transform linear;
}

.breath-phase {
  margin: 8px 0 0;
  text-align: center;
  font-size: 16px;
  font-weight: 600;
  color: var(--col-primary-dk);
}

.breath-count {
  margin: 2px 0 0;
  text-align: center;
  font-size: 26px;
  font-weight: 700;
  color: var(--col-accent);
  min-height: 32px;
}

.breath-round {
  margin: 0;
  text-align: center;
  font-size: 12px;
  color: var(--col-sub);
  min-height: 18px;
}

.breath-btns {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 12px;
}

.btn-primary {
  border: none;
  border-radius: 999px;
  padding: 8px 26px;
  background: var(--col-primary);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.btn-soft {
  border: 1px solid var(--col-line);
  border-radius: 999px;
  padding: 8px 26px;
  background: var(--col-chip);
  color: var(--col-text);
  font-size: 14px;
  cursor: pointer;
}
</style>
