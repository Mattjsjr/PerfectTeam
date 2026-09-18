import {z} from 'zod';
import {zodResolver} from '@hookform/resolvers/zod';

export const schema = z.object({
    numericalFromZero : z.number().min(1, 'Must be at least 1').max(24, 'Maximum of 24 teams').min(1, 'This field is required'),
    numericalAny : z.number().max(1000000, 'Maximum of 1000000')
})

