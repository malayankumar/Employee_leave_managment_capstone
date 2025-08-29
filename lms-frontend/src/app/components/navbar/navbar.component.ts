import { Component } from '@angular/core';
@Component({
  selector: 'app-navbar',
  templateUrl: './navbar.component.html'
})
export class NavbarComponent {
  name = localStorage.getItem('name') || 'User';
  role = localStorage.getItem('role') || 'EMPLOYEE';
  logout(){ localStorage.clear(); location.href='/login'; }
}
