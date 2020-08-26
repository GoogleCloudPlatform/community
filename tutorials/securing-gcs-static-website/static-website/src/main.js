import Vue from 'vue';
import App from './App.vue';
import 'semantic-ui-css/semantic.min.css';

var VueCookie = require('vue-cookie');
// Tell Vue to use the plugin
Vue.use(VueCookie);

Vue.config.productionTip = false;

new Vue({
  render: h => h(App)
}).$mount('#app');
