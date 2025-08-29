import { Component } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { UserService } from '../../core/user.service';

@Component({
  selector: 'app-register-employee',
  templateUrl: './register-employee.component.html'
})
export class RegisterEmployeeComponent {
  saving = false;
  msg = '';
  err = '';

  form = this.fb.group({
    name: ['', [Validators.required]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(5)]],
  });

  constructor(private fb: FormBuilder, private users: UserService) {}

  submit() {
    if (this.form.invalid) return;
    this.saving = true; this.msg = ''; this.err = '';
    const { name, email, password } = this.form.value as any;

    this.users.createEmployee(name, email!, password!).subscribe({
      next: () => {
        this.msg = 'Employee registered successfully';
        this.saving = false;
        this.form.reset();
      },
      error: (e) => {
        this.err = e?.error?.message || 'Failed to register employee';
        this.saving = false;
      }
    });
  }
}
