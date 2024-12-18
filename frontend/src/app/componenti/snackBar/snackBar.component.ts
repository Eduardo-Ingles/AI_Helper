import {Component, inject, Input} from '@angular/core';
import {MatSnackBar} from '@angular/material/snack-bar';
import {MatButtonModule} from '@angular/material/button';
import {MatInputModule} from '@angular/material/input';
import {MatFormFieldModule} from '@angular/material/form-field';

/**
 * @title Basic snack-bar
 */
@Component({
    standalone: true,
    selector: 'snack-bar-overview-example',
    templateUrl: 'snackBar.component.html',
    styleUrl: 'snackBar.component.css',
    imports: [MatFormFieldModule, MatInputModule, MatButtonModule],
})
export class SnackBarOverviewExample {
    private _snackBar = inject(MatSnackBar);

    @Input() messaggio = ""
    openSnackBar() {
        this._snackBar.open(this.messaggio);
    }
}
