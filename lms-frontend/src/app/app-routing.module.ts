import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { LoginComponent } from './pages/login/login.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { RequestLeaveComponent } from './pages/request-leave/request-leave.component';
import { MyLeavesComponent } from './pages/my-leaves/my-leaves.component';
import { ApprovalsComponent } from './pages/approvals/approvals.component';
import { RegisterEmployeeComponent } from './pages/register-employee/register-employee.component';
import { AuthGuard } from './core/auth.guard';
import { RoleGuard } from './core/role.guard';

const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: '', component: DashboardComponent, canActivate: [AuthGuard] },
  { path: 'request', component: RequestLeaveComponent, canActivate: [AuthGuard] },
  { path: 'my-leaves', component: MyLeavesComponent, canActivate: [AuthGuard] },
  { path: 'approvals', component: ApprovalsComponent, canActivate: [AuthGuard, RoleGuard], data: { role: 'MANAGER' } },
  { path: 'register-employee', component: RegisterEmployeeComponent, canActivate: [RoleGuard], data: { role: 'MANAGER' } },
  { path: '**', redirectTo: '' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule {}
