<template>
  <div class="ui grid">
    <div class="centered row">
      <div class="five wide column"></div>
      <div class="six wide centered aligned column"><h1>{{ msg }}</h1></div>
      <div class="five wide column"></div>
    </div>
    <div class="centered row">
      <div class="five wide column"></div>
      <div class="six wide centered aligned column">
      <p>
        <button
          id="login-button"
          class="ui primary button"
          role="button"
          v-on:click="logout()"
        >Logout</button>
      </p></div>
      <div class="five wide column"></div>
    </div>
    <div class="centered row">
      <div class="five wide column"></div>
      <div class="six wide column"><img alt="Arch image" src="../assets/arch-gcs-site.png" /></div>
      <div class="five wide column"></div>
    </div><div class="row">
        <div class="five wide column"></div>
        <div class="six wide left aligned column">
      <h3>The solution used by this demo</h3>
      <ul>
        <li>
          1. Determine if there is a signed cookie from the user request. If the cookie doesn't exist in the header,
          redirect the user to the Login page hosted on Cloud Run. If there is a signed cookie, send the request
          to the backend bucket.
        </li>
      </ul>
      <ul>
        <li>2. After successfully authenticating the user, send a signed cookie in the response.</li>
      </ul>
      <ul>
        <li>
          3. The load balancer needs a custom domain with a valid ssl certificate. A URL map needs to be configured
          so that the unauthenticated request will be sent to the login page, and authenticated ones will be sent to
          the backend bucket.
          <b>The signed cookie approach works because both backends are under the same domain.</b>
        </li>
      </ul>
      <ul>
        <li>4. Permit Cloud CDN to read the objects by adding the Cloud CDN service account to Cloud Storage's ACLs.</li>
      </ul>
      <h3>References</h3>
      <ul>
        <li>
          <a
            href="https://cloud.google.com/storage/docs/hosting-static-website"
            target="_blank"
            rel="noopener"
          >Cloud Storage - Hosting a static website</a>
        </li>
      </ul>
      <ul>
        <li>
          <a
            href="https://cloud.google.com/load-balancing/docs/https/ext-load-balancer-backend-buckets"
            target="_blank"
            rel="noopener"
          >Setting up a load balancer with backend buckets</a>
        </li>
      </ul>
      <ul>
        <li>
          <a
            href="https://cloud.google.com/cdn/docs/setting-up-cdn-with-bucket"
            target="_blank"
            rel="noopener"
          >Setting up Cloud CDN with a backend bucket</a>
        </li>
      </ul>
      <ul>
        <li>
          <a
            href="https://cloud.google.com/cdn/docs/using-signed-cookies#configuring_permissions"
            target="_blank"
            rel="noopener"
          >Allow Cloud CDN to read objects in a private Cloud Storage bucket</a>
        </li>
      </ul>
      <ul>
        <li>
          <a
            href="https://cloud.google.com/load-balancing/docs/negs/serverless-neg-concepts"
            target="_blank"
            rel="noopener"
          >Google Cloud HTTP(S) Load Balancing for Serverless Computing (Beta) - Concept</a>
        </li>
      </ul>
      <ul>
        <li>
          <a
            href="https://cloud.google.com/load-balancing/docs/negs/setting-up-serverless-negs"
            target="_blank"
            rel="noopener"
          >Cloud Load Balancing - Setting up serverless NEGs (Beta) - How-to guide</a>
        </li>
      </ul>
      <ul>
        <li>
          <a
            href="https://cloud.google.com/cdn/docs/using-signed-cookies"
            target="_blank"
            rel="noopener"
          >Cloud CDN - Using signed cookies</a>
        </li>
      </ul>
      <ul>
        <li>
          <a
            href="https://cloud.google.com/compute/docs/reference/rest/v1/urlMaps/insert?hl=en#request-body"
            target="_blank"
            rel="noopener"
          >UrlMaps API</a>
        </li>
      </ul>
      <ul>
        <li>
          <a
            href="https://cloud.google.com/load-balancing/docs/https/setting-up-query-and-header-routing#http-header-based-routing"
            target="_blank"
            rel="noopener"
          >Setting up custom header based routing</a>
        </li>
      </ul>
      </div>
      <div class="five wide column"></div>
    </div>
  </div>
</template>

<script>
export default {
  name: "HelloWorld",
  props: {
    msg: String
  },
  methods: {
    logout () {
      this.$cookie.delete('Cloud-CDN-Cookie')
      window.location.href = window.location.origin + '/logout';
    }
  }
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
h3 {
  margin: 40px 0 0;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
.hello {
  width: 50%;
  left: 25%;
  position: relative;
}
.arch {
  position: relative;
  display: inline-block;
  vertical-align: top;
  width: auto;
  text-align: left;
}
</style>
