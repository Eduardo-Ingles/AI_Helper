import {Component, inject, Input, Output, EventEmitter} from '@angular/core';
import {Dialog, DialogModule, DialogRef} from '@angular/cdk/dialog';
import {MatTooltipModule} from '@angular/material/tooltip';
import {MatIconModule} from '@angular/material/icon';
import { CommonModule } from '@angular/common';
import { HttpClient , HttpClientModule} from '@angular/common/http';

import { environment } from '../../../enviroments/environment';


import {
    MAT_DIALOG_DATA,
    MatDialog,
    MatDialogActions,
    MatDialogClose,
    MatDialogContent,
    MatDialogTitle,
} from '@angular/material/dialog'

@Component({
  selector: 'custom-dialog-box-display',
  templateUrl: 'customDialogBoxDisplay.component.html',
  styleUrl: 'customDialogBoxDisplay.component.css',
  standalone: true,
  imports: [DialogModule, MatTooltipModule, MatIconModule],
})
export class CustomDialogBoxDisplay {
    //dialog = inject(Dialog);
    tooltipValue = "cliccami per maggiori informazioni oppure per semplice curiosità!"
    //openDialog_(): void {
    //    this.dialog.open<string>(CustomDialogBoxDisplayContent);
    //}
    @Input() tutorialText: string = "";
    @Input() exampleFile: string = "";
    
    showLink: boolean = true;
    dialog = inject(MatDialog);
    openDialog() {
        if(this.exampleFile != ""){
            this.showLink = true;
        }else{
            this.showLink = false;
        }
        //console.log("exampleFile:", this.exampleFile, "showLink: ",this.showLink);
        this.dialog.open(CustomDialogBoxDisplayContent, {data: {data: this.tutorialText, exampleFile: this.exampleFile, showLink: this.showLink}, 
            maxWidth: '80vw',
            maxHeight: '90vh',
            //height: '100%',
            //width: '100%',
            panelClass: 'full-screen-modal'
        });
        //console.log(msg)
    }

}


@Component({
    selector: 'custom-dialog-box-display-content',
    templateUrl: 'customDialogBoxDisplay.component-content.html',
    styleUrl: 'customDialogBoxDisplay.component-content.css',
    standalone: true,
    imports: [MatIconModule, CommonModule, HttpClientModule],
})
export class CustomDialogBoxDisplayContent {

	constructor(private apiService: HttpClient) {}
    
    @Output() fileDownload = new EventEmitter<any>();
  
    exampleFile = inject(MAT_DIALOG_DATA).exampleFile;
    showLink = inject(MAT_DIALOG_DATA).showLink;
    tutorialText = inject(MAT_DIALOG_DATA).data;


    downloadFile(filePath: string) {
        // Assuming the backend has a download endpoint
        const downloadEndpoint = `download/${filePath}`;
        this.apiService.get(`${environment.api}/${downloadEndpoint}`, {
            responseType: 'blob'
        }).subscribe({
            next: (response) => {
                // Create a blob from the response
                const blob = new Blob([response], { type: 'application/octet-stream' });   
				//console.log("Response: ", response);
                // Create a link element and trigger download
                const link = document.createElement('a');
				link.href = URL.createObjectURL(blob);
                link.href = window.URL.createObjectURL(blob);
                link.download = this.exampleFile;
                link.click();
            },
            error: (err) => {
                console.error('Download failed', err);
            }
        });
    }

    dialogRef = inject(DialogRef);


}

