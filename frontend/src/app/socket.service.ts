import { Injectable } from '@angular/core';
import { io, Socket } from 'socket.io-client';
import { environment } from '../enviroments/environment'; // Update with your environment config

@Injectable({
  providedIn: 'root',
})
export class SocketService {
  private socket: Socket;

  constructor() {
    this.socket = io(environment.ip + ":" + environment.porta); // Your FastAPI backend URL
  }

  // Listen for events from the server
  listen(eventName: string, callback: (data: any) => void) {
    this.socket.on(eventName, callback);
  }

  // Emit events to the server
  emit(eventName: string, data: any) {
    this.socket.emit(eventName, data);
  }

  // Disconnect the socket
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
    }
  }
}
