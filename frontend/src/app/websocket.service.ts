import { Injectable } from '@angular/core';
import { WebSocketSubject, webSocket } from 'rxjs/webSocket';
import { Observable, Subject, catchError, tap, EMPTY } from 'rxjs';

import { v4 as uuidv4 } from 'uuid';
import { environment } from '../enviroments/environment';

interface WebSocketMessage {
    sender: string;
    message: string;
    timestamp: string;
}

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
    private socket$: WebSocketSubject<any>;
    private messagesSubject = new Subject<WebSocketMessage>();
    private clientId: string;

    constructor() {
        // Generate a unique client ID
        this.clientId = uuidv4();
        this.socket$ = this.createWebSocket();
        //console.log('WebSocketService constructed with client ID:', this.clientId);
        this.initWebSocket();
        
    }

    private initWebSocket() {
        //console.log('Initializing WebSocket connection');
        this.socket$ = webSocket({
            url: `${environment.ws}/${this.clientId}`,
            openObserver: {
                next: () => console.log(`WebSocket connection opened for client ${this.clientId}`)
            },
            closeObserver: {
                next: () => console.log(`WebSocket connection closed for client ${this.clientId}`)
            }
        });
        this.socket$.subscribe({
            next: (msg) => {
                try {                        
                    const parsedMsg: WebSocketMessage = msg;
                    //console.log('Received WebSocket message:', parsedMsg);
                    this.messagesSubject.next(parsedMsg);
                } catch (error) {
                    console.warn('Received non-JSON message:', msg);
                    // Handle the non-JSON message appropriately (e.g., log it, ignore it, or display a warning to the user).
                }
                },
                error: (err) => console.error('WebSocket error:', err),
                complete: () => console.log('WebSocket connection completed')
            });
      }
    
    private createWebSocket(): WebSocketSubject<any> {
        return webSocket({
        url: "${environment.ws}/${this.clientId}",
        openObserver: {
            next: () => console.log(`WebSocket connection opened for client ${this.clientId}`)
        },
        closeObserver: {
            next: () => console.log(`WebSocket connection closed for client ${this.clientId}`)
        }
        });

    }

    sendMessage(msg: string) {
        try {
          this.socket$.next(msg);
          //console.log(`Message sent by client ${this.clientId}:`, msg);
        } catch (error) {
          console.error('Failed to send message:', error);
        }
      }
    

    getClientId(): string {
        return this.clientId;
    }

    // Receive messages
    getMessages(): Observable<WebSocketMessage> {
        return this.messagesSubject.asObservable(); 
    }

    // Close connection
    close() {
        this.socket$.complete();
    }
}