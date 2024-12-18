import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  	providedIn: 'root', // This makes the service available app-wide
})
export class SharedDataService {
	// Use BehaviorSubject to keep track of the value and provide observable access
	private sharedValueSource = new BehaviorSubject<string>('');
	
	// Observable to allow components to subscribe and get the current value
	sharedValue$ = this.sharedValueSource.asObservable();

	// Method to update the shared value
	updateSharedValue(newValue: string): void {
		this.sharedValueSource.next(newValue);
	}
}


@Injectable({
	providedIn: 'root', // This makes the service available app-wide
})
export class SharedDataServiceDict {
	// Initialize BehaviorSubject with an empty object as the default value
	private sharedValueSource = new BehaviorSubject<Record<string, any>>({});
  
	// Observable to allow components to subscribe and get the current dictionary value
	sharedValue$ = this.sharedValueSource.asObservable();
  
	// Method to update the entire shared dictionary
	updateSharedValue(newValue: Record<string, any>): void {
	  	this.sharedValueSource.next(newValue);
	}
  
	// Method to update a specific key-value pair in the dictionary
	updateSharedKey(key: string, value: any): void {
	  const currentData = this.sharedValueSource.value;
	  this.sharedValueSource.next({ ...currentData, [key]: value });
	}
}