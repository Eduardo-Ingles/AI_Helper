import { Component, OnInit, OnDestroy } from '@angular/core';
import { WebSocketService } from '../websocket.service';
import { Subscription } from 'rxjs';

import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-websocket-client',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="container">
      <div class="message-list">
        <div *ngFor="let msg of messages" class="message">
          <!--strong>{{ msg.sender }}:</strong--> {{ msg.message }}
          <!--small>({{ msg.timestamp | date:'mediumTime' }})</small-->
        </div>
      </div>
      <div class="input-area">
        <input 
          type="text"
          [(ngModel)]="newMessage" 
          (keyup.enter)="sendMessage()"
          placeholder="Type a message..."
        />
        <button (click)="sendMessage()">Send</button>
      </div>
    </div>
  `,
  styles: [`
    .container { 
    position: absolute;
    top: 50%;
    left: 50%;
      max-width: 600px; 
      margin: auto; 
      padding: 20px; 
    }
    .message-list { 
      height: 300px; 
      overflow-y: scroll; 
      border: 1px solid #ccc; 
      margin-bottom: 10px; 
    }
    .message { 
      padding: 5px; 
      border-bottom: 1px solid #eee; 
    }
    .input-area { 
      display: flex; 
    }
    input { 
      flex-grow: 1; 
      margin-right: 10px; 
    }
  `]
})
export class WebSocketClientComponent implements OnInit, OnDestroy {
    messages: any[] = [];
    newMessage = '';
    messageSubscription: Subscription = Subscription.EMPTY;

    constructor(private wsService: WebSocketService) {
    //console.log('WebSocketClientComponent constructed');
    }

    ngOnInit() {
    //console.log('WebSocketClientComponent initialized');
    this.messageSubscription = this.wsService.getMessages()
        .subscribe(msg => {
        //console.log('Received message:', msg);
        this.messages.push(msg);
        });
    }

    sendMessage() {
    if (this.newMessage.trim()) {
        //console.log('Sending message:', this.newMessage);
        this.wsService.sendMessage(this.newMessage);
        this.newMessage = '';
    }
    }

    ngOnDestroy() {
    if (this.messageSubscription) {
        this.messageSubscription.unsubscribe();
    }
    this.wsService.close();
    }
}