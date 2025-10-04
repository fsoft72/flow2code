/**
 * User table schema for Drizzle ORM
 * Defines the structure for user authentication and profile data
 */
export const users = sqliteTable( 'users', {
	/**
	 * Unique identifier for the user
	 */
	id: text( 'id' ).primaryKey().$defaultFn( () => '' ).notNull(),

	/**
	 * Domain associated with the user account
	 */
	domain: text( 'domain', { length: 50 } ),

	/**
	 * Email address of the user
	 */
	email: text( 'email', { length: 200 } ),

	/**
	 * Username for the user account (required)
	 */
	username: text( 'username', { length: 50 } ).notNull(),

	/**
	 * First name of the user
	 */
	name: text( 'name', { length: 50 } ),

	/**
	 * Last name of the user
	 */
	lastname: text( 'lastname', { length: 50 } ),

	/**
	 * User permissions stored as a JSON array of strings
	 */
	perms: text( 'perms', { mode: 'json' } ).$type<string[] | null>(),

	/**
	 * Whether the user account is enabled (1) or disabled (0)
	 */
	enabled: integer( 'enabled' ),

	/**
	 * User access level (numerical value)
	 */
	level: integer( 'level' ),

	/**
	 * Hashed password for user authentication
	 */
	password: text( 'password', { length: 64 } ),

	/**
	 * Verification or temporary code for user operations
	 */
	code: text( 'code', { length: 64 } ),

	/**
	 * Refresh token for authentication
	 */
	refresh_token: text( 'refresh_token', { length: 64 } ),

	/**
	 * Account creation timestamp
	 */
	created: text( 'created' ).default( sql`CURRENT_TIMESTAMP` ),

	/**
	 * Last account update timestamp
	 */
	updated: text( 'updated' ).default( sql`CURRENT_TIMESTAMP` ),
}, ( table: any ) => [
	/**
	 * Index on domain field for efficient domain-based queries
	 */
	index( 'idx_user_domain' ).on( table.domain ),

	/**
	 * Index on enabled field for filtering active/inactive users
	 */
	index( 'idx_user_enabled' ).on( table.enabled ),

	/**
	 * Index on email field for user lookup by email
	 */
	index( 'idx_user_email' ).on( table.email ),

	/**
	 * Index on username field for user lookup by username
	 */
	index( 'idx_user_username' ).on( table.username ),
]
);

/**
 * Type inference for User table select operations
 */
export type User = typeof users.$inferSelect;