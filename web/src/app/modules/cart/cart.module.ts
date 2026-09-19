import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CartRoutingModule } from './cart-routing.module';
import { CartPageComponent } from './pages/cart-page/cart-page.component';
import { MapPickerComponent } from './components/map-picker/map-picker.component';

@NgModule({
  declarations: [
    CartPageComponent,
    MapPickerComponent
  ],
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    CartRoutingModule
  ]
})
export class CartModule { }