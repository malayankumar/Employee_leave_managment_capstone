import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class UserService {
  private base = environment.apiBase;   // '/api' in docker

  constructor(private http: HttpClient) {}

  createEmployee(name: string, email: string, password: string) {
    return this.http.post(`${this.base}/users`, {
      name, email, password, role: 'EMPLOYEE'
    });
  }
  listUsers(){
    return this.http.get(`${this.base}/users`);
  }
}
