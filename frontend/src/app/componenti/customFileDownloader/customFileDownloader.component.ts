import { Component, OnInit } from '@angular/core';
import { DomSanitizer } from '@angular/platform-browser';

@Component({
    standalone: true,
    selector: 'custom-fileDnld-app',
    templateUrl: './customFileDownloader.component.html',
    styleUrls: ['./customFileDownloader.component.css']
})
export class CustomFileDownloader implements OnInit {
    name = 'Angular 5';
    fileUrl:any;
    constructor(private sanitizer: DomSanitizer) {  }
    ngOnInit() {
        const data = 'some text';
        const blob = new Blob([data], { type: 'application/octet-stream' });
        this.fileUrl = this.sanitizer.bypassSecurityTrustResourceUrl(window.URL.createObjectURL(blob));
    }

}
