(function (window) {
  window.env = window.env || {};
  // Environment variable
  // window['env']['apiurl'] = '${API_URL}';
  // doing below work around for lint issue and replacing above line
  window['env']['apiurl'] = `${''}\${API_URL}`;
})(this);
