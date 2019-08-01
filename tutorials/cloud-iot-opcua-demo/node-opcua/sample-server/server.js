const opcua = require("node-opcua");
const config = require("./server_config.json");

const server = new opcua.OPCUAServer({
    port: config.port, // the port of the listening socket of the server
    resourcePath: config.resourcePath, // this path will be added to the endpoint resource name
     buildInfo : {
        productName: config.buildInfo.productName,
        buildNumber: config.buildInfo.buildNumber,
        buildDate: new Date(2019,6,16)
    },
    alternateHostname: config.alternateHostname
});

function addObjectTo(addressSpace, object) {
  const namespace = addressSpace.getOwnNamespace();
  const serverObject = namespace.addObject({
    organizedBy: addressSpace.rootFolder.objects,
    browseName: object.browseName
  });
  for(let variable of object.metaData) {
    namespace.addVariable({
      componentOf: serverObject,
      browseName: variable.browseName,
      dataType: variable.dataType,
      value: {
        get: () => {
          return new opcua.Variant({dataType: opcua.DataType[variable.dataType], value: variable.value });
        }
      }
    });
  }
  let counter = 0;
  setInterval(() => {counter=Math.floor(Math.random() * (object.value.max-object.value.min+1))+object.value.min}, object.value.updatefrequency);
  namespace.addVariable({
    componentOf: serverObject,
    browseName: object.value.browseName,
    dataType: object.value.dataType,
    value: {
        get: () => {
            return new opcua.Variant({dataType: opcua.DataType[object.value.dataType], value: counter });
        }
    }
  });
}

function post_initialize() {
    console.log("initialized");
    function construct_my_address_space(server) {
      const addressSpace = server.engine.addressSpace;
      for(let object of config.objects) {
        addObjectTo(addressSpace, object);
      }
    }
    construct_my_address_space(server);
    server.start(function() {
        console.log("Server is now listening ... ( press CTRL+C to stop)");
        console.log("port ", server.endpoints[0].port);
        const endpointUrl = server.endpoints[0].endpointDescriptions()[0].endpointUrl;
        console.log(" the primary server endpoint url is ", endpointUrl );
    });
}
server.initialize(post_initialize);

