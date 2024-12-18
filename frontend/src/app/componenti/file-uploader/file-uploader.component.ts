import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {MatSnackBar} from '@angular/material/snack-bar';

import { HttpClient } from '@angular/common/http';
import { environment } from '../../../enviroments/environment';

import { SharedDataServiceDict } from './../../shared-data.service';
import { stringify } from 'uuid';

@Component({
    selector: 'app-file-uploader',
    templateUrl: './file-uploader.component.html',
    styleUrls: ['./file-uploader.component.css'],
    imports: [CommonModule, FormsModule],
    standalone: true
})
export class FileUploaderComponent {
	loadComplete = false;

    private _snackBar = inject(MatSnackBar);

	constructor(private apiService: HttpClient, 
		private sharedDataServiceDict: SharedDataServiceDict
	) {}

	@Input() allowMultipleFiles: boolean = false; // Control single or multiple file uploads
	@Input() selectedFiles: File[] = []; // Store selected files in memory

	@Output() filesSaved = new EventEmitter<File[]>(); // Emit an array of files

	@Input() snackDefMsg = " caricato con successo!"
    openSnackBar_(files: string) {
        this._snackBar.open(files + this.snackDefMsg);
    }
	openSnackBar(messaggio: string) {
		this._snackBar.open(messaggio + this.snackDefMsg, "chiudi", {duration: 5000});
	}


	handleFileInput(event: Event) {
		const input = event.target as HTMLInputElement;
		const files = input?.files ? Array.from(input.files) : []; // Convert FileList to File[]
		this.filesSaved.emit(files); // Emit the File[] array
		this.filesSaved.emit(this.selectedFiles);
	}
	
	// File selection handler
	onFileSelected(event: Event) {
		const input = event.target as HTMLInputElement;
		if (input?.files) {
		const files = Array.from(input.files);
		this.selectedFiles = this.allowMultipleFiles ? files : [files[0]];
		}
		//console.log("selectedFiles:", this.selectedFiles)
		if(this.selectedFiles.length === 0){
			this.clearFiles();
		}
	}

	// Upload a single file
	uploadFiles() {
		if (this.selectedFiles.length === 0) {
			this.selectedFiles = [];
			//console.error('No files selected');
			this.sharedDataServiceDict.updateSharedValue({fileNames: []});
			return;
		}

		if (this.selectedFiles.length === 1) {
			const formData = new FormData();
			this.selectedFiles.forEach(file => {
			formData.append('file', file); // Append each file to the form data
			});

			this.apiService.post(`${environment.api}/upload-single`, formData).subscribe({
			next: (response) => console.log('Upload successful:', response),
			error: (err) => console.error('Upload failed:', err)
			});
		}
		if (this.selectedFiles.length > 1) {
			const formData = new FormData();
			this.selectedFiles.forEach(file => {
			formData.append('files', file); // Append each file to the form data
			});

			this.apiService.post(`${environment.api}/upload-multiple`, formData).subscribe({
			next: (response) => console.log('Upload successful:', response),
			error: (err) => console.error('Upload failed:', err)
			});			
		}

		if(this.selectedFiles.length != 0){
			const fileNames = this.selectedFiles.map(file => file.name);
			//console.log("File Names:", fileNames);			
			this.openSnackBar((fileNames).toString());
			this.sharedDataServiceDict.updateSharedValue({fileNames: fileNames});
		}
	}

	clearFiles(){
		const formData = new FormData();
		if(this.selectedFiles.length != 0){
			this.selectedFiles = [];
		}
		this.selectedFiles = [];
		this.sharedDataServiceDict.updateSharedValue({fileNames: []});
		//console.log("clearFiles: ", this.selectedFiles)
	}
	

}
