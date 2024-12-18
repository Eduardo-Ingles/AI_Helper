// src/environments/environment.ts (for development)

const serverIp = "172.16.212.107";
//const serverIp = "192.168.1.82";
const serverPort = "5001";

export const environment = {
    production: false,
    ip: serverIp,
    porta: serverPort,
    api: 'http://' + serverIp + ':' + serverPort + '/api',  //
    ws: "ws://' + serverIp + ':' + serverPort + '/ws",    //
};
  
  // src/environments/environment.prod.ts (for production)
export const environmentProd = {
    production: true,
    ip: serverIp,
    porta: serverPort,
    api: 'http://' + serverIp + ':' + serverPort + '/api',  //
    ws: "ws://' + serverIp + ':' + serverPort + '/ws",    //
};