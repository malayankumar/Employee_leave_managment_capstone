import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class LeaveService {
  private api = environment.apiBase; // e.g. http://localhost:8081/api

  constructor(private http: HttpClient) {}

  // canonical method
  requestLeave(data: any): Observable<any> {
    return this.http.post(`${this.api}/leaves`, data);
  }

  // alias so existing components using createLeave keep working
  createLeave(data: any): Observable<any> {
    return this.requestLeave(data);
  }

  myLeaves(): Observable<any[]> {
    return this.http.get<any[]>(`${this.api}/leaves/mine`);
  }

  pending(): Observable<any[]> {
    return this.http.get<any[]>(`${this.api}/leaves/pending`);
  }

  approve(id: number, remark: string = ''): Observable<any> {
  return this.http.post(`${this.api}/leaves/${id}/approve`, { remark });
  }

  reject(id: number, remark: string = ''): Observable<any> {
    return this.http.post(`${this.api}/leaves/${id}/reject`, { remark });
  }

  getMyBalance(year?: number){
  const url = year ? `${this.api}/leaves/balance?year=${year}` : `${this.api}/leaves/balance`;
  return this.http.get<any>(url);
  }

  getAllBalances(year?: number){ // MANAGER only
    const url = year ? `${this.api}/leaves/balance/all?year=${year}` : `${this.api}/leaves/balance/all`;
    return this.http.get<any[]>(url);
  }

  getUserBalance(userId: number, year?: number){ // MANAGER only
    const url = year ? `${this.api}/leaves/balance/${userId}?year=${year}` : `${this.api}/leaves/balance/${userId}`;
    return this.http.get<any>(url);
  }
  
  create(p: { type: string; start_date: string; end_date: string; reason?: string }) {
  return this.http.post<any>(`${this.api}/leaves`, p);
  }



}
