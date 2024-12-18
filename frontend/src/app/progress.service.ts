import { Injectable } from '@angular/core';
import { environment } from '../enviroments/environment';

@Injectable({
  providedIn: 'root'
})
export class ProgressService {
 	private socket: WebSocket | undefined;

  	connect(): WebSocket {
    	if(!this.socket || this.socket.readyState !== WebSocket.OPEN) {
    		this.socket = new WebSocket(`${environment.ws}/progress`);
    	}
    	return this.socket;
  	}
/*
	connect(clientId: string | null): WebSocket {
    	if(!this.socket || this.socket.readyState !== WebSocket.OPEN) {
    		this.socket = new WebSocket(`${environment.ws}/progress/${clientId}`);
    	}
    	return this.socket;
  	}*/
	/*

	connect(clientId: string): WebSocket {
		return new WebSocket(`${environment.ws}/progress/${clientId}`);
	}*/
}
