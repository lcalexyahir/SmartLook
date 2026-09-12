import { NgModule } from '@angular/core';
import { RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';


// Componentes compartidos
import { LoadingSpinnerComponent } from './components/loading-spinner/loading-spinner.component';
import { ProductCardComponent } from './components/product-card/product-card.component';
import { ModalComponent } from './components/modal/modal.component';


// Directivas
import { HighlightDirective } from './directives/highlight.directive';


// Pipes
import { CurrencyFormatPipe } from './pipes/currency-format.pipe';
import { DateFormatPipe } from './pipes/date-format.pipe';



@NgModule({

  declarations: [

    LoadingSpinnerComponent,

    ProductCardComponent,

    ModalComponent,


    HighlightDirective,


    CurrencyFormatPipe,

    DateFormatPipe,

  ],


  imports: [

    CommonModule,

    FormsModule,

    ReactiveFormsModule,

  ],


  exports: [

    CommonModule,

    FormsModule,

    ReactiveFormsModule,


    LoadingSpinnerComponent,

    ProductCardComponent,

    ModalComponent,


    HighlightDirective,


    CurrencyFormatPipe,

    DateFormatPipe,

  ]

})


export class SharedModule {

}