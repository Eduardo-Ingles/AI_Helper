
import { HttpClient, HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError  } from 'rxjs';
import { Injectable } from '@angular/core';
import { environment } from '../enviroments/environment';

import { catchError, retry } from 'rxjs/operators';

@Injectable({
  providedIn: 'root',
})
export class ApiTest {
    
    protected baseUrl = environment.api;

    constructor(private http: HttpClient) { }

    private handleError(error: HttpErrorResponse) {
        let errorMessage = 'An error occurred';
        if (error.error instanceof ErrorEvent) {
          // Client-side error
          errorMessage = error.error.message;
        } else {
          // Server-side error
          errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
        }
        console.error(errorMessage);
        return throwError(() => new Error(errorMessage));
      }

    private getHttpOptions(responseType: 'json' | 'text' = 'json') {
        return {
        headers: new HttpHeaders({
            'Content-Type': 'application/json',
        }),
        responseType: responseType as 'json',
        };
    }

    // You can add common HTTP methods here
    //protected get<T>(endpoint: string) {
    //    return this.http.get<T>(`${this.baseUrl}/${endpoint}`);
    //}


    // HTTP GET method
    //public get<T>(endpoint: string): Observable<T> {
    //    return this.http.get<T>(`${this.baseUrl}/${endpoint}`);
    //}
    public get<T>(endpoint: string): Observable<T> {
        return this.http.get<T>(`${this.baseUrl}/${endpoint}`);
    }

    // HTTP POST method
    //protected post<T>(endpoint: string, data: any) {
    //    return this.http.post<T>(`${this.baseUrl}/${endpoint}`, data);
    //}
    //public post<T>(endpoint: string, data: any): Observable<T> {
    //    return this.http.post<T>(`${this.baseUrl}/${endpoint}`, data);
    //}

    public post<T>(endpoint: string, data: any): Observable<T> {
      console.log('Sending request to:', `${this.baseUrl}/${endpoint}`);
      console.log('Request body:', data);
  
      return this.http.post<T>(`${this.baseUrl}/${endpoint}`, data)
          .pipe(retry(1),
              catchError(error => {
                  console.log('Request failed:', error);
                  return throwError(error);
              })
          );
  }

    // Enhanced HTTP POST method
    //public post<T>(endpoint: string, data: any, responseType: 'json' | 'text' = 'json'): Observable<T> {
    //    return this.http.post<T>(
    //    `${this.baseUrl}/${endpoint}`,
    //    data,
    //    this.getHttpOptions(responseType)
    //    ).pipe(
    //    retry(1),
    //    catchError(this.handleError)
    //    );
    //}

    // HTTP PUT method
    //protected put<T>(endpoint: string, data: any) {
    //    return this.http.put<T>(`${this.baseUrl}/${endpoint}`, data);
    //}
    public put<T>(endpoint: string, data: any): Observable<T> {
        return this.http.put<T>(`${this.baseUrl}/${endpoint}`, data);
    }

    // HTTP DELETE method
    //protected delete<T>(endpoint: string) {
    //    return this.http.delete<T>(`${this.baseUrl}/${endpoint}`);
    //}
    public delete<T>(endpoint: string): Observable<T> {
        return this.http.delete<T>(`${this.baseUrl}/${endpoint}`);
    }
}

@Injectable({
  providedIn: 'root',
})
export class WebSocketService {
  private socket!: WebSocket;

  connect(): void {
    this.socket = new WebSocket(environment.ws);

    this.socket.onmessage = (event) => {
      console.log('Received:', event.data);
    };
  }

  sendMessage(message: string): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      	this.socket.send(message);
    }
  }
}