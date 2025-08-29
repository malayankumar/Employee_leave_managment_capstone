import { Injectable } from '@angular/core';
import {
  HttpInterceptor,
  HttpRequest,
  HttpHandler,
  HttpEvent,
} from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth.service';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(private auth: AuthService) {}

  private isApiUrl(url: string): boolean {
    // Adjust if your API base is different
    // Works for relative "/api/..." and absolute "http(s)://.../api/..."
    return /(^\/api\/)|(^https?:\/\/[^/]+\/api\/)/i.test(url);
  }

  private isLoginUrl(url: string): boolean {
    return /\/api\/auth\/login$/i.test(url);
  }

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    let headers = req.headers;

    // 1) Only attach token for our API (not 3rd-party) and not for login
    const shouldAttachToken = this.isApiUrl(req.url) && !this.isLoginUrl(req.url);

    if (shouldAttachToken && !headers.has('Authorization')) {
      const token =
        typeof (this.auth as any).token === 'function'
          ? (this.auth as any).token()
          : localStorage.getItem('token');

      if (token) {
        headers = headers.set('Authorization', `Bearer ${token}`);
      }
    }

    // 2) Don’t force Content-Type unless it’s a JSON body we’re sending
    const methodHasBody = !['GET', 'HEAD', 'OPTIONS'].includes(req.method.toUpperCase());
    const isFormData = typeof FormData !== 'undefined' && req.body instanceof FormData;

    if (
      methodHasBody &&
      !isFormData &&
      !headers.has('Content-Type') &&
      req.body !== null &&
      req.body !== undefined
    ) {
      headers = headers.set('Content-Type', 'application/json');
    }

    // 3) Clone with updated headers
    const authReq = req.clone({ headers });
    return next.handle(authReq);
  }
}
