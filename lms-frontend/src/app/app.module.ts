import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';

import { LoginComponent } from './pages/login/login.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { RequestLeaveComponent } from './pages/request-leave/request-leave.component';
import { MyLeavesComponent } from './pages/my-leaves/my-leaves.component';
import { ApprovalsComponent } from './pages/approvals/approvals.component';
import { NavbarComponent } from './components/navbar/navbar.component';
import { RegisterEmployeeComponent } from './pages/register-employee/register-employee.component'; // 👈 new

import { AuthInterceptor } from './core/auth.interceptor';

@NgModule({
  declarations: [
    AppComponent,
    LoginComponent,
    DashboardComponent,
    RequestLeaveComponent,
    MyLeavesComponent,
    ApprovalsComponent,
    NavbarComponent,
    RegisterEmployeeComponent
  ],
  imports: [
    BrowserModule,
    HttpClientModule,
    FormsModule,
    ReactiveFormsModule,       
    AppRoutingModule
  ],
  providers: [
    { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true }
  ],
  bootstrap: [AppComponent]
})
export class AppModule {}
