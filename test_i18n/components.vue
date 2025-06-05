<template>
  <div class="app">
    <h1>{{ $t('common.welcome') }}</h1>
    <nav>
      <a href="/">{{ $t('navigation.home') }}</a>
      <a href="/about">{{ $t('navigation.about') }}</a>
      <a href="/contact">{{ $t('navigation.contact') }}</a>
    </nav>
    
    <div class="login-form">
      <h2>{{ $t('auth.login.title') }}</h2>
      <input :placeholder="$t('auth.login.username')" />
      <input :placeholder="$t('auth.login.password')" type="password" />
      <button>{{ $t('auth.login.submit') }}</button>
    </div>
    
    <div class="errors">
      <p v-if="showError">{{ $t('errors.404') }}</p>
      <!-- 这个键不存在 -->
      <p v-if="showNetworkError">{{ $t('errors.network.connection') }}</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      showError: false,
      showNetworkError: false
    }
  },
  methods: {
    showMessage() {
      // 使用存在的键
      this.$message.success(this.$t('common.hello'));
      
      // 使用不存在的键
      this.$message.info(this.$t('messages.info.saved'));
    }
  }
}
</script> 