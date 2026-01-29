<script setup>
import { useUserStore } from './stores/user'

const userStore = useUserStore()
</script>

<template>
  <router-view />
</template>

<style>
#app {
  width: 100%;
  min-height: 100vh;
}
</style>
