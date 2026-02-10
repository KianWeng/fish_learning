<template>
  <view class="tree-children" :style="{ paddingLeft: (depth * 24) + 'rpx' }">
    <view
      v-for="(node, i) in nodes"
      :key="i"
      class="tree-node"
    >
      <view class="node-row">
        <text class="node-bullet">·</text>
        <text class="node-label">{{ node.label || '子节点' }}</text>
        <text class="node-meta" v-if="nodeMeta(node)">{{ nodeMeta(node) }}</text>
      </view>
      <KnowledgeTree
        v-if="node.children && node.children.length"
        :nodes="node.children"
        :depth="depth + 1"
      />
    </view>
  </view>
</template>

<script setup>
const props = defineProps({
  nodes: { type: Array, default: () => [] },
  depth: { type: Number, default: 0 }
})

function nodeMeta(node) {
  if (!node) return ''
  const count = node.count
  const mastered = node.mastered
  if (count != null && mastered != null) return `${mastered}/${count} 已掌握`
  if (count != null) return `${count} 题`
  return ''
}
</script>

<style scoped>
.tree-children { margin-top: 4rpx; }
.tree-node { margin-bottom: 8rpx; }
.node-row { display: flex; align-items: baseline; flex-wrap: wrap; }
.node-bullet { font-size: 26rpx; color: var(--primary); margin-right: 8rpx; }
.node-label { font-size: 26rpx; color: var(--text); }
.node-meta { font-size: 22rpx; color: var(--text-hint); margin-left: 12rpx; }
</style>
