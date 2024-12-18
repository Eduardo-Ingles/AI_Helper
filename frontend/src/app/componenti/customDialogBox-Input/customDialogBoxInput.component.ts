import {Component, inject} from '@angular/core';
import {Dialog, DialogRef, DIALOG_DATA, DialogModule} from '@angular/cdk/dialog';
import {FormsModule} from '@angular/forms';

export interface DialogData {
    galleria: string;
    name: string;
}

@Component({
    selector: 'custom-dialog-box-input',
    templateUrl: 'customDialogBoxInput.component.html',
    standalone: true,
    imports: [FormsModule, DialogModule],
})
export class CustomDialogBoxInput {
    dialog = inject(Dialog);

    galleria: string | undefined;
    name: string | undefined;

    openDialog(): void {
        const dialogRef = this.dialog.open<string>(CustomDialogBoxInputContent, {
        width: '250px',
        data: {name: this.name, animal: this.galleria},
        });

        dialogRef.closed.subscribe(result => {
        console.log('The dialog was closed');
        this.galleria = result;
        });
    }
}

@Component({
    selector: 'custom-dialog-box-input-content',
    templateUrl: 'customDialogBoxInput-content.component.html',
    styleUrl: 'customDialogBoxInput-content.component.css',
    standalone: true,
    imports: [FormsModule],
})
export class CustomDialogBoxInputContent {
    dialogRef = inject<DialogRef<string>>(DialogRef<string>);
    data = inject(DIALOG_DATA);
}