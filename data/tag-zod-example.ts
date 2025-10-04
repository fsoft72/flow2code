/**
 * Schema for adding new tags to the system
 *
 * @property {string} name - Required tag name (min 1 character)
 * @property {string} [slug] - Optional URL-friendly slug (auto-generated if not provided)
 * @property {string} [description] - Optional tag description
 * @property {string} [color] - Optional hex color code (must be valid 6-digit hex)
 * @property {string} [category] - Optional tag category for organization
 * @property {number} [weight=1.0] - Tag weight for relevance calculations (0-10, default 1.0)
 * @property {string} [updated_by] - Optional user ID who created/updated the tag
 */
const AddTagSchema = z.object( {
	name: z.string().min( 1, 'Tag name is required' ),
	slug: z.string().optional(),
	description: z.string().optional(),
	color: z.string().regex( /^#[0-9A-Fa-f]{6}$/, 'Color must be a valid hex code' ).optional(),
	category: z.string().optional(),
	weight: z.coerce.number().min( 0 ).max( 10 ).default( 1.0 ),
	updated_by: z.string().optional(),
} );
