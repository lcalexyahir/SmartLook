import { Pipe, PipeTransform } from '@angular/core';


@Pipe({
  name: 'currencyFormat'
})
export class CurrencyFormatPipe implements PipeTransform {


  transform(value: number | string | null | undefined): string {

    if (value === null || value === undefined || value === '') {

      return 'Bs 0.00';

    }


    return `Bs ${Number(value).toFixed(2)}`;

  }

}