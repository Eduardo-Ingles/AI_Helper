import { Component } from '@angular/core';
import { RouterModule, RouterOutlet, RouterLink, Routes } from '@angular/router';
import {AppRoutingModule } from '../app.routes'
import {MatIconModule} from '@angular/material/icon';


@Component({
  selector: 'app-custom-nav-bar',
  standalone: true,
  imports: [ RouterModule, MatIconModule ],
  templateUrl: './custom-nav-bar.component.html',
  styleUrl: './custom-nav-bar.component.css'
})
export class CustomNavBarComponent {

}
