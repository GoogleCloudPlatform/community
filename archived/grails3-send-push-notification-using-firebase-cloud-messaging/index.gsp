<!doctype html>
<html>
<head>
  <meta name="layout" content="main"/>
  <title>FCM Sender</title>

  <asset:link rel="icon" href="favicon.ico" type="image/x-ico" />
</head>
<body>
  <div id="content" role="main">
      <section class="row colset-2-its">
          <h1>Send Push Notification</h1>
          <g:if test="${flash.message}">
            <div class="message" role="alert">
              ${flash.message}
            </div>
          </g:if>
          <g:form action="sendPushNotification">
            <fieldset>
              <div class="fieldcontain">
                <label for="regid">FCM Registration ID</label>
                <g:textField name="regid" />
              </div>
              <div class="fieldcontain">
                <label for="title">Title</label>
                <g:textField name="title" />
              </div>
              <div class="fieldcontain">
                <label for="body">Message Body</label>
                <g:textField name="body" />
              </div>
            </fieldset>
            <fieldset>
              <div class="buttons">
                <g:submitButton class="save" name="submit" value="Send" />
              </div>
            </fieldset>
          </g:form>
      </section>
  </div>
</body>
</html>