import { Injectable } from '@angular/core';
import { CanActivate, ActivatedRouteSnapshot, Router } from '@angular/router';
import { AuthService } from './auth.service';

@Injectable({ providedIn: 'root' })
export class RoleGuard implements CanActivate {
  constructor(private auth: AuthService, private router: Router) {}
  canActivate(route: ActivatedRouteSnapshot) {
    const need = route.data['role'];
    if (this.auth.role() === need) return true;
    this.router.navigate(['/']); return false;
  }
}
