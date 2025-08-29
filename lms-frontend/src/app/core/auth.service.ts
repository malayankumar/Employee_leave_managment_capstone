import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private api = environment.apiBase;

  constructor(private http: HttpClient) {}

  login(email: string, password: string): Observable<{token: string, role: string, name: string}> {
    return this.http.post<{token: string, role: string, name: string}>(`${this.api}/auth/login`, { email, password });
  }

  saveSession(token: string, role: string, name: string) {
    localStorage.setItem('token', token);
    localStorage.setItem('role', role);
    localStorage.setItem('name', name);
  }

  logout() {
    localStorage.clear();
  }

  isLoggedIn() { return !!localStorage.getItem('token'); }
  role() { return localStorage.getItem('role') || 'EMPLOYEE'; }
  token() { return localStorage.getItem('token') || ''; }
  name() { return localStorage.getItem('name') || 'User'; }
}
