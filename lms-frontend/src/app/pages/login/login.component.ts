import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../core/auth.service';

@Component({ selector: 'app-login', templateUrl: './login.component.html' })
export class LoginComponent {
  email='manager@example.com'; password='12345'; error='';
  constructor(private auth: AuthService, private router: Router) {}
  submit(){
    this.auth.login(this.email, this.password).subscribe({
      next: r => { this.auth.saveSession(r.token, r.role, r.name); this.router.navigate(['/']); },
      error: _ => this.error = 'Invalid credentials'
    });
  }
}
